"""Operator-only Chromium probe, streamed into an idle worker via Docker exec.

Never copied into the worker image, exposed as a tool, or fed report text/GT.
Host injects only fixed fixture metadata and synthetic object IDs via argv.
"""
import asyncio
import base64
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.parse import quote, urlsplit
from uuid import UUID, uuid4

import httpx
from playwright.async_api import async_playwright, Error as PlaywrightError

from boundary.contracts import LAB_IP, ORIGIN
from worker.browser_tool import LAUNCH_ARGS


async def probe(config: dict, results: list[dict], diagnostics: dict) -> list[dict]:
    # Fixed operator fixture parameters; no arbitrary URL, JavaScript or expression.
    point = config["point"]
    if point not in {f"XSS-{i:02}" for i in range(1, 8)}:
        raise ValueError("UNKNOWN_POINT")
    UUID(config["snapshot_id"])
    UUID(config["run_id"])
    obj = config["objects"]["requester-a"]
    for field in ("request_id", "item_id", "supplier_id"):
        UUID(obj[field])
    # CASE_SOURCE is inserted from the repository-owned mapping by the host runner.
    accounts = json.loads(Path("/run/secrets/lab_accounts").read_text())
    async with httpx.AsyncClient(base_url=f"http://{LAB_IP}:8001", trust_env=False, follow_redirects=False,
            timeout=10, headers={"Host": "lab:8001", "Origin": ORIGIN, "Accept-Encoding": "identity"}) as client:
        async def login(alias: str) -> dict:
            client.cookies.clear()
            response = await client.post("/api/auth/login", json={"login_name": alias, "password": accounts[alias]["password"]})
            response.raise_for_status()
            value = response.json()
            if value.get("account_alias") != alias:
                raise ValueError("IDENTITY_MISMATCH")
            client.headers["X-CSRF-Token"] = value["csrf_token"]
            return {"actor_alias": alias, "user_id": value["user_id"]}

        async with async_playwright() as pw:
            diagnostics["stage"] = "launch"
            browser = await pw.chromium.launch(channel="chromium", headless=True, chromium_sandbox=True, args=LAUNCH_ARGS)
            try:
                for kind in ("inert", "marker", "safe"):
                    diagnostics["fixture"] = kind
                    async with asyncio.timeout(30):
                        nonce, action_id, evidence_id = (str(uuid4()) for _ in range(3))
                        payload = fixture(point, nonce, inert=kind == "inert")
                        writes, relative = case(point, config["objects"], payload, safe=kind == "safe")
                        write_evidence = []
                        writer = None
                        if writes:
                            diagnostics["stage"] = "writer_login"
                            writer = await login("requester-a")
                            for method, target in writes:
                                response = await client.request(method, target, json={"value": payload})
                                response.raise_for_status()
                                write_evidence.append({"method": method, "path": target, "status": response.status_code,
                                    "actor": writer, "input_sha256": hashlib.sha256(payload.encode()).hexdigest(),
                                    "response_sha256": hashlib.sha256(response.content).hexdigest()})
                        diagnostics["stage"] = "reader_login"
                        reader = await login("requester-b")
                        if writer and writer["user_id"] == reader["user_id"]:
                            raise ValueError("IDENTITY_MISMATCH")
                        url = ORIGIN + relative + ("#" + quote(payload, safe="") if point == "XSS-07" else "")
                        diagnostics["stage"] = "new_context"
                        context = await browser.new_context(viewport={"width": 800, "height": 600},
                            service_workers="block", accept_downloads=False)
                        events, pending, background = [], set(), []
                        counters = {"documents": 0, "denied": 0, "websockets": 0, "popups": 0, "downloads": 0}
                        closing = False
                        page = None
                        page_response = {}
                        try:
                            if await context.cookies():
                                raise ValueError("SESSION_ISOLATION_FAILED")
                            await context.add_init_script("Object.defineProperty(window,'__vvStorageEmpty',{value:localStorage.length===0&&sessionStorage.length===0});")
                            await context.add_cookies([{"name": c.name, "value": c.value, "url": ORIGIN,
                                "httpOnly": True, "sameSite": "Strict"} for c in client.cookies.jar])

                            async def route_request(route):
                                task = asyncio.current_task()
                                pending.add(task)
                                try:
                                    request = route.request
                                    if (closing or request.url != url.split("#")[0] or request.method != "GET" or
                                            request.resource_type != "document" or request.frame != page.main_frame or
                                            request.redirected_from or counters["documents"]):
                                        counters["denied"] += 1
                                        await route.abort("blockedbyclient")
                                        return
                                    counters["documents"] += 1
                                    # No browser-native forwarding, redirects, arbitrary hosts or subresources.
                                    async with client.stream("GET", relative) as response:
                                        if response.status_code != 200 or response.headers.get("content-encoding", "identity") != "identity":
                                            raise ValueError("DOCUMENT_FAILED")
                                        raw = bytearray()
                                        async for chunk in response.aiter_bytes():
                                            if len(raw) + len(chunk) > 1048576:
                                                raise ValueError("DOCUMENT_LIMIT")
                                            raw.extend(chunk)
                                        page_response.update(status=response.status_code, sha256=hashlib.sha256(raw).hexdigest())
                                        await route.fulfill(status=200, content_type="text/html; charset=utf-8", body=bytes(raw),
                                            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
                                except asyncio.CancelledError:
                                    try:
                                        await route.abort("blockedbyclient")
                                    except PlaywrightError:
                                        pass
                                    if not closing:
                                        raise
                                finally:
                                    pending.discard(task)

                            await context.route("**/*", route_request)

                            async def websocket(ws):
                                counters["websockets"] += 1
                                await ws.close(code=1008, reason="POLICY_BLOCKED")
                            await context.route_web_socket("**/*", websocket)

                            async def marker(source, value):
                                if (value == nonce and source["page"] == page and source["frame"] == page.main_frame and
                                        source["frame"].url == url and urlsplit(source["frame"].url).netloc == "lab:8001" and not events):
                                    events.append({"nonce": nonce, "origin": ORIGIN, "path": urlsplit(url).path,
                                        "frame": "main", "captured_at": time.time()})
                            await context.expose_binding("__vvMarker", marker)

                            def new_page(opened):
                                if page is not None and opened != page:
                                    counters["popups"] += 1
                                    background.append(asyncio.create_task(opened.close()))
                            context.on("page", new_page)
                            diagnostics["stage"] = "new_page"
                            page = await context.new_page()

                            def download(item):
                                counters["downloads"] += 1
                                background.append(asyncio.create_task(item.cancel()))
                            page.on("download", download)
                            diagnostics["stage"] = "navigation"
                            await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                            await page.locator("html[data-ready='true']").wait_for(timeout=2000)
                            await page.wait_for_timeout(200)
                            js = await page.evaluate("() => 6 * 7") == 42
                            empty = await page.evaluate("() => window.__vvStorageEmpty") is True
                            # Fixed locator and expression only; attribute controls must preserve exact value.
                            visible = (await page.locator("#probe").input_value() if point == "XSS-06"
                                else await page.locator("#probe").text_content()) == payload
                            diagnostics["stage"] = "screenshot"
                            png = await page.screenshot(type="png", full_page=False, timeout=3000)
                            if len(png) > 262144:
                                raise ValueError("SCREENSHOT_LIMIT")
                            excerpt = (await page.locator("body").inner_text())[:8192]
                            results.append({"run_id": config["run_id"], "snapshot_id": config["snapshot_id"],
                                "action_id": action_id, "evidence_id": evidence_id, "source": "operator_chromium",
                                "kind": kind, "nonce": nonce, "path": urlsplit(url).path, "query_sha256": hashlib.sha256(urlsplit(url).query.encode()).hexdigest(),
                                "writer": writer, "reader": reader, "writes": write_evidence, "response": page_response,
                                "browser_version": browser.version, "sandbox_requested": True,
                                "js_control": js, "initial_storage_empty": empty, "payload_visible_as_text": visible,
                                "marker_events": events.copy(), "counters": counters.copy(), "dom_excerpt": excerpt,
                                "screenshot_base64": base64.b64encode(png).decode(), "screenshot_sha256": hashlib.sha256(png).hexdigest(),
                                "captured_at": time.time()})
                        finally:
                            diagnostics["last_stage"] = diagnostics["stage"]
                            closing = True
                            running = list(pending)
                            for task in running:
                                task.cancel()
                            await asyncio.gather(*running, return_exceptions=True)
                            await context.close()
                            await asyncio.gather(*background, return_exceptions=True)
            finally:
                await browser.close()
    return results


async def main() -> None:
    config = json.loads(sys.argv[1])
    results = []
    diagnostics = {"stage": "startup"}
    output = {"status": "RUNNING", "observations": results, "diagnostics": diagnostics}
    try:
        async with asyncio.timeout(95):
            await probe(config, results, diagnostics)
        output["status"] = "PASS"
    except Exception as exc:
        # Keep earlier captures without logging login payloads/cookies or arbitrary exception text.
        output.update(status="FAILED", error_type=type(exc).__name__)
    print(json.dumps(output))


if __name__ == "__main__":
    asyncio.run(main())
