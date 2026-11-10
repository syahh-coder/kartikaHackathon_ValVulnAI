import json

from app.common import uid


class BodyLimitMiddleware:
    """Bound streamed JSON/multipart before framework parsing, including chunked bodies."""
    def __init__(self, app, maximum: int = 262144):
        self.app, self.maximum = app, maximum

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] in {"GET", "HEAD", "OPTIONS"}:
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            data = message.get("body", b"")
            size += len(data)
            if size > self.maximum:
                body = json.dumps({"request_id": uid(), "error_code": "REQUEST_LIMIT", "message": "Body terlalu besar.",
                                   "field_errors": [], "retryable": False}).encode()
                await send({"type": "http.response.start", "status": 413,
                            "headers": [(b"content-type", b"application/json"), (b"cache-control", b"no-store")]})
                await send({"type": "http.response.body", "body": body})
                return
            chunks.append(data)
            if not message.get("more_body", False):
                break
        delivered = False
        async def bounded_receive():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
        await self.app(scope, bounded_receive, send)
