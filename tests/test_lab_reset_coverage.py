import sqlite3

import pytest

from lab.maintenance import reset
from lab.xss_catalog import POINTS
from lab.uploads import POINTS as UPLOAD_POINTS

ACCOUNTS = {alias: {"password": "synthetic-coverage-test-password"} for alias in ["requester-a", "requester-b"]}


async def test_legacy_selected_reset_does_not_enable_other_points(tmp_path):
    path = tmp_path/"lab.sqlite3"
    await reset(path, ACCOUNTS, "vulnerable", xss_point="XSS-01", point_condition="vulnerable")
    with sqlite3.connect(path) as conn:
        settings = dict(conn.execute("SELECT key,value FROM settings"))
    assert settings["delete_owner_check"] == "0"
    assert settings["notification_dom_html"] == "0"
    assert settings["catalog_search_html"] == "1"
    assert all(settings[key] == "0" for point,key in POINTS.items() if point != "XSS-01")
    assert all(settings[key] == "0" for key in UPLOAD_POINTS.values())


async def test_conflicting_global_and_selected_reset_rejected_before_write(tmp_path):
    path = tmp_path/"lab.sqlite3"
    with pytest.raises(ValueError, match="not both"):
        await reset(path, ACCOUNTS, "vulnerable", all_supported=True, xss_point="XSS-01")
    assert not path.exists()
