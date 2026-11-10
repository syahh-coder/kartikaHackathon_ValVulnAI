"""Private operator route/input mapping, never imported by app, planner or worker."""
from urllib.parse import urlencode


POINTS = tuple(f"XSS-{i:02}" for i in range(1, 8))


def case(point: str, objects: dict, payload: str, *, safe: bool = False) -> tuple[list[tuple[str, str]], str]:
    obj = objects["requester-a"]
    request_id, item_id, supplier_id = (obj[k] for k in ("request_id", "item_id", "supplier_id"))
    if point == "XSS-01":
        return [], "/catalog/search?" + urlencode({"q": payload, "view": "text" if safe else "result"})
    if point == "XSS-02":
        return [("PATCH", f"/api/catalog/items/{item_id}/note")], f"/catalog/items/{item_id}?field=" + ("description" if safe else "note")
    if point == "XSS-03":
        return [("PATCH", f"/api/requests/{request_id}/reason")], f"/requests/{request_id}/review?view=" + ("audit" if safe else "review")
    if point == "XSS-04":
        return [("PATCH", "/api/profile/display-name"), ("POST", f"/api/requests/{request_id}/comments")], f"/requests/{request_id}/comments?field=" + ("body" if safe else "name")
    if point == "XSS-05":
        return [("PATCH", f"/api/suppliers/{supplier_id}/name")], "/suppliers?" + urlencode({"supplier_id": supplier_id, "field": "code" if safe else "name"})
    if point == "XSS-06":
        return [], "/tracking?" + urlencode({"ref": payload, "view": "text" if safe else "tracking"})
    if point == "XSS-07":
        return [], "/requests/view?view=" + ("text" if safe else "detail")
    raise ValueError("Unknown operator point")


def fixture(point: str, nonce: str, *, inert: bool = False) -> str:
    if inert:
        return "Kontrol inert ValVuln " + nonce
    marker = f"window.__vvMarker('{nonce}')"
    if point == "XSS-06":
        # Escape the quoted value and create an image with a local error callback.
        return '\"><img src="data:image/png;base64,AA==" onerror="' + marker + '"><input value="'
    return '<img src="data:image/png;base64,AA==" onerror="' + marker + '">'
