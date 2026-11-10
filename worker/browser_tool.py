"""One fixed DOM-XSS probe per fresh sandboxed browser/context, no arbitrary eval API."""
import asyncio
import base64
import hashlib
import json
import time
from urllib.parse import quote

import httpx

from boundary.browser import BrowserCapture, MarkerEvent, allowed_browser_url, fixture_text
from boundary.contracts import ActionEnvelope, BrowserObservation, LAB_IP, ORIGIN


LAUNCH_ARGS = ["--host-resolver-rules=MAP lab 172.30.74.3", "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]


class BrowserTool:
    def __init__(self, accounts: dict):
        self.accounts = accounts

    async def execute(self, envelope: ActionEnvelope, envelope_hash: str, boot_id: str) -> BrowserObservation:
        # Playwright is installed only in the worker image, never required by app/HTTP tests.
        from playwright.async_api import Error as PlaywrightError, async_playwright
        args = envelope.validated_arguments
        capture = BrowserCapture(fixture=args.fixture, nonce=args.nonce, path=args.relative_path, browser_version="not-started")
        attempts, responses, http_status = 0, 0, None
        status, error = "OK", None
        secrets = [a["password"] for a in self.accounts.values()]
        payload = fixture_text(args)
        browser_started = False
        try:
            envelope.authorize()
            async with asyncio.timeout(max(.001, envelope.expires_at-time.time())):
                async with httpx.AsyncClient(base_url=f"http://{LAB_IP}:8001", trust_env=False, follow_redirects=False,
                        timeout=10, headers={"Host": "lab:8001", "Origin": ORIGIN, "Accept-Encoding": "identity"}) as client:
                    attempts += 1
                    async with client.stream("POST", "/api/auth/login", json={"login_name": args.account_alias,
                            "password": self.accounts[args.account_alias]["password"]}) as response:
                        responses += 1
                        raw = bytearray()
                        async for chunk in response.aiter_bytes():
                            if len(raw)+len(chunk)>4096: raise ValueError("AUTH_FAILED")
                            raw.extend(chunk)
                        identity = json.loads(raw)
                        if response.status_code != 200 or identity.get("account_alias") != args.account_alias:
                            raise ValueError("AUTH_FAILED")
                    secrets.extend([identity.get("csrf_token", ""), *[c.value for c in client.cookies.jar]])
                    async with async_playwright() as pw:
                        browser = await pw.chromium.launch(channel="chromium", headless=True, chromium_sandbox=True, args=LAUNCH_ARGS)
                        browser_started = True
                        capture.browser_version = browser.version
                        context = await browser.new_context(viewport={"width": 800, "height": 600},
                                service_workers="block", accept_downloads=False)
                        tasks = []
                        routing = set()
                        closing = False
                        page = None
                        try:
                            if await context.cookies(): raise ValueError("SESSION_ISOLATION_FAILED")
                            await context.add_init_script("Object.defineProperty(window, '__vvStorageEmpty', {value: localStorage.length === 0 && sessionStorage.length === 0});")
                            await context.add_cookies([{"name": c.name, "value": c.value, "url": ORIGIN,
                                "httpOnly": True, "sameSite": "Strict"} for c in client.cookies.jar])
                            async def forward_request(route):
                                nonlocal attempts, responses, http_status, error
                                if closing:
                                    await route.abort("blockedbyclient")
                                    return
                                request = route.request
                                # Every browser network request is mediated through bounded HTTPX,
                                # pinned to the literal lab IP. All subresources/popups are denied here.
                                if (not allowed_browser_url(request.url, args) or request.method != "GET" or
                                        request.resource_type != "document" or request.frame != page.main_frame or
                                        request.redirected_from or attempts >= min(2, envelope.network_remaining)):
                                    capture.denied_requests = min(40, capture.denied_requests+1)
                                    await route.abort("blockedbyclient")
                                    return
                                try:
                                    envelope.authorize()
                                    attempts += 1
                                    async with client.stream("GET", args.relative_path) as response:
                                        responses += 1
                                        http_status = response.status_code
                                        if 300 <= response.status_code < 400: raise ValueError("REDIRECT_BLOCKED")
                                        if response.headers.get("content-encoding", "identity") != "identity":
                                            raise ValueError("ENCODING_DENIED")
                                        raw = bytearray()
                                        async for chunk in response.aiter_raw():
                                            if len(raw)+len(chunk)>1048576: raise ValueError("RESPONSE_LIMIT")
                                            raw.extend(chunk)
                                        await route.fulfill(status=response.status_code, body=bytes(raw), headers={
                                            "Content-Type": response.headers.get("content-type", "text/html"),
                                            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
                                except (ValueError, httpx.HTTPError):
                                    error = "BROWSER_NETWORK_FAILED"
                                    if not closing: await route.abort("failed")
                            async def route_request(route):
                                task = asyncio.current_task()
                                routing.add(task)
                                try:
                                    await forward_request(route)
                                except asyncio.CancelledError:
                                    # A callback that returns without handling its route
                                    # leaves Playwright's outer handled_future pending.
                                    # Abort while interception is still installed.
                                    try:
                                        await route.abort("blockedbyclient")
                                    except PlaywrightError:
                                        pass
                                    if not closing: raise
                                except PlaywrightError:
                                    if not closing: raise
                                finally:
                                    routing.discard(task)
                            await context.route("**/*", route_request)
                            async def websocket(ws):
                                capture.websocket_blocks = min(40, capture.websocket_blocks+1)
                                await ws.close(code=1008, reason="POLICY_BLOCKED")
                            await context.route_web_socket("**/*", websocket)
                            async def marker(source, nonce):
                                if (page is not None and source["page"] == page and source["frame"] == page.main_frame
                                        and allowed_browser_url(source["frame"].url, args) and nonce == str(args.nonce)
                                        and args.fixture == "marker-v1" and not capture.marker_events):
                                    capture.marker_events.append(MarkerEvent(nonce=args.nonce, origin=ORIGIN,
                                        path=args.relative_path, frame="main"))
                            await context.expose_binding("__vvMarker", marker)
                            def new_page(opened):
                                if page is not None and opened != page:
                                    capture.popup_blocks = min(40, capture.popup_blocks+1)
                                    tasks.append(asyncio.create_task(opened.close()))
                            context.on("page", new_page)
                            page = await context.new_page()
                            def download(item):
                                capture.download_blocks = min(40, capture.download_blocks+1)
                                tasks.append(asyncio.create_task(item.cancel()))
                            page.on("download", download)
                            page.on("dialog", lambda dialog: tasks.append(asyncio.create_task(dialog.dismiss())))
                            fragment = "#"+quote(payload, safe="") if args.operation == "notification_probe" else ""
                            await page.goto(ORIGIN+args.relative_path+fragment, wait_until="domcontentloaded", timeout=10000)
                            await page.locator("#preview[data-ready='true']").wait_for(timeout=2000)
                            # Fixed instrumentation only; callers cannot provide an expression.
                            capture.js_control = await page.evaluate("() => 6 * 7") == 42
                            capture.initial_storage_empty = await page.evaluate("() => window.__vvStorageEmpty") is True
                            if not capture.initial_storage_empty: raise ValueError("SESSION_ISOLATION_FAILED")
                            await page.wait_for_timeout(200)
                            capture.payload_visible_as_text = await page.locator("#preview").text_content() == payload
                            text = await page.locator("body").inner_text(timeout=1000)
                            for secret in secrets:
                                if secret: text = text.replace(secret, "[REDACTED]")
                            capture.dom_excerpt = text[:8192]
                            screenshot = await page.screenshot(type="png", full_page=False, timeout=3000)
                            if len(screenshot)>262144: raise ValueError("SCREENSHOT_LIMIT")
                            capture.screenshot_base64 = base64.b64encode(screenshot).decode("ascii")
                            capture.screenshot_sha256 = hashlib.sha256(screenshot).hexdigest()
                        finally:
                            closing = True
                            # Removing routes while a document is paused releases it to
                            # Chromium's own network stack. Keep interception installed
                            # until the context is closed, including during cancellation.
                            pending = list(routing)
                            for task in pending: task.cancel()
                            await asyncio.gather(*pending, return_exceptions=True)
                            await context.close()
                            await asyncio.gather(*tasks, return_exceptions=True)
                            await browser.close()
                    if error: raise ValueError(error)
        except asyncio.CancelledError:
            status, error = "CANCELLED", "CANCELLED"
        except TimeoutError:
            status, error = "FAILED", "BROWSER_TIMEOUT"
        except ValueError as exc:
            code = str(exc)
            status, error = "FAILED", code if code in {"AUTH_FAILED", "SCREENSHOT_LIMIT", "ARTIFACT_LIMIT", "BROWSER_NETWORK_FAILED", "ACTION_EXPIRED", "POLICY_BLOCKED", "SESSION_ISOLATION_FAILED"} else "RESPONSE_SCHEMA_ERROR"
        except PlaywrightError:
            status, error = "FAILED", "BROWSER_FAILED" if browser_started else "BROWSER_SANDBOX_UNAVAILABLE"
        except Exception:
            status, error = "FAILED", "INTERNAL_TOOL_ERROR"
        body = capture.model_dump_json()
        if len(body.encode())+4096 > envelope.artifact_remaining:
            status, error = "FAILED", "ARTIFACT_LIMIT"
            capture.screenshot_base64, capture.screenshot_sha256 = "", ""
            capture.dom_excerpt = ""
            body = capture.model_dump_json()
        return BrowserObservation(run_id=envelope.run_id, action_id=envelope.action_id, action_seq=envelope.action_seq,
            envelope_hash=envelope_hash, target_snapshot_id=envelope.target_snapshot_id, boot_id=boot_id,
            status=status, error_code=error, http_status=http_status, actor_alias=args.account_alias, method="GET",
            relative_path=args.relative_path, body=body, body_sha256=hashlib.sha256(body.encode()).hexdigest(),
            request_attempts=attempts, responses_received=responses, captured_at=time.time())


class ToolRouter:
    def __init__(self, accounts):
        from worker.http_tool import HttpTool
        from worker.upload_tool import UploadTool
        self.http, self.browser = HttpTool(accounts), BrowserTool(accounts)
        self.upload = UploadTool(accounts)

    async def execute(self, envelope, fingerprint, boot_id):
        tool = self.browser if envelope.tool_name == "browser_probe" else self.upload if envelope.tool_name == "upload_fixture" else self.http
        return await tool.execute(envelope, fingerprint, boot_id)
