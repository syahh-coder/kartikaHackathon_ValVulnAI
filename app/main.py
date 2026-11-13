import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import auth
from app.api import routes
from app.api import runs
from app.api import business_records
from app.api import triage
from app.agent.text_triage import TextTriage
from app.agent.workflow import Workflow
from app.common import AppError, error_response, uid
from app.validation_errors import safe_field_errors
from app.middleware import BodyLimitMiddleware
from app.storage.lock import ProcessLock

from app.config import Settings
from app.storage.db import Database, all_rows


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    db = Database(config.db_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        lock = ProcessLock(config.data_dir)
        task = None
        try:
            await db.migrate()
            await app.state.workflow.recover()
            await app.state.text_triage.recover()
            if config.dispatcher_enabled:
                task = asyncio.create_task(app.state.workflow.loop())
            yield
        finally:
            await app.state.text_triage.close()
            app.state.workflow.stop_event.set()
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            lock.close()

    app = FastAPI(title="ValVuln AI", version="0.1.0", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.config = config
    app.state.db = db
    app.state.workflow = Workflow(db, config)
    app.state.text_triage = TextTriage(db, config)
    app.add_middleware(BodyLimitMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[urlsplit(config.public_origin).hostname])
    app.include_router(auth.router)
    app.include_router(routes.router)
    app.include_router(runs.router)
    app.include_router(business_records.router)
    app.include_router(triage.router)
    app.add_exception_handler(AppError, error_response)
    templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
    app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

    @app.get("/", include_in_schema=False)
    async def index(request: Request):
        return templates.TemplateResponse(request, "workspace.html", {})

    @app.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception):
        return await error_response(request, AppError(500, "INTERNAL_ERROR", "Terjadi kesalahan aplikasi. Periksa catatan operator."))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Pydantic error objects may include passwords or report text; do not echo input.
        return await error_response(request, AppError(422, "SCHEMA_ERROR", "Periksa isian formulir yang ditandai.",
                                                       field_errors=safe_field_errors(exc)))

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return await error_response(request, AppError(exc.status_code, "HTTP_ERROR", "Permintaan tidak dapat diproses."))

    @app.middleware("http")
    async def response_headers(request: Request, call_next):
        request.state.request_id = uid()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        return response

    @app.get("/api/health")
    async def health():
        async with db.connect() as conn:
            rows = await all_rows(conn, "SELECT version FROM schema_versions ORDER BY version")
        return {"status": "ok", "schema_versions": [r["version"] for r in rows]}

    @app.get("/api/readiness")
    async def readiness():
        from app.providers.contracts import ProviderFailure
        from app.providers.triage_contracts import MAX_INPUT_TOKENS, MAX_OUTPUT_TOKENS, SCHEMA_VERSION
        from app.providers.text_provider import require_configuration
        try:
            require_configuration(config)
            text_status = "CONFIGURED_NOT_VERIFIED" if config.triage_mode == "live" else "MOCK"
        except ProviderFailure as exc:
            text_status = exc.code
        text_readiness = {"triage_mode": config.triage_mode, "text_provider": text_status,
                          "lab_planner_mode": config.execution_mode,
                          "triage_provider": config.triage_provider if config.triage_mode == "live" else config.triage_mode,
                          "triage_requested_model": config.triage_model if config.triage_mode == "live" else "mock-triage-v1",
                          "provider_priority": ["openrouter", "azure"], "automatic_provider_fallback": False,
                          "triage_input_tokens": MAX_INPUT_TOKENS, "triage_output_tokens": MAX_OUTPUT_TOKENS,
                          "triage_schema_version": SCHEMA_VERSION, "ai_validation_draft": "HUMAN_CONFIRMATION_REQUIRED"}
        if config.transport_key_file:
            try:
                from app.transport import Handoff
                heartbeat=await asyncio.to_thread(lambda:Handoff(db,config).heartbeat())
                async with db.connect() as conn:
                    from app.storage.db import one
                    target=await one(conn,"SELECT ready,dirty,maintenance,snapshot_id FROM target_bindings WHERE target_id='portal-lab'")
                lab=("OPERATOR_VERIFIED" if target and target["ready"] and not target["dirty"] and not target["maintenance"] and not heartbeat["dirty"] and
                     target["snapshot_id"]==heartbeat["snapshot_id"] else "OPERATOR_CHECK_REQUIRED")
                return {**text_readiness,"app":"ready","mode":config.execution_mode,"worker":heartbeat["status"],"lab":lab,
                        "live_provider":"CONFIGURATION_REQUIRED","lab_validation_from_ui":"AVAILABLE", "lab_tools":"HTTP_BOUNDED_BROWSER_AND_UPLOAD_FIXTURES"}
            except (OSError,ValueError,KeyError,AppError):
                return {**text_readiness,"app":"ready","mode":config.execution_mode,"worker":"NOT_READY","lab":"OPERATOR_CHECK_REQUIRED",
                        "live_provider":"CONFIGURATION_REQUIRED","lab_validation_from_ui":"DEPENDENCY_NOT_READY", "lab_tools":"HTTP_BOUNDED_BROWSER_AND_UPLOAD_FIXTURES"}
        return {**text_readiness,"app": "ready", "mode": config.execution_mode, "worker": "NOT_IMPLEMENTED",
                "lab": "NOT_IMPLEMENTED", "live_provider": "CONFIGURATION_REQUIRED"}

    return app
