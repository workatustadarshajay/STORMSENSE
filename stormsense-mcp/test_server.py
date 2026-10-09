"""Checks the MCP tools against a stand-in StormSense API: right path, headers and error mapping.

Run:  uv run --group dev pytest -q
"""

from __future__ import annotations

import asyncio
import json

import httpx

import server


def _api(handler) -> httpx.MockTransport:
    server.TRANSPORT = httpx.MockTransport(handler)
    return server.TRANSPORT


def _run(coro):
    return json.loads(asyncio.run(coro))


def test_read_tool_sends_planner_identity_and_filters():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["email"] = request.headers["x-forwarded-email"]
        return httpx.Response(200, json={"urgent_transfers": 2})

    _api(handler)
    result = _run(server.stormsense_overview())
    assert result == {"urgent_transfers": 2}
    assert seen["email"] == server.PLANNER_EMAIL
    assert seen["url"].endswith("/api/overview")


def test_list_transfers_drops_unset_filters():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json=[])

    _api(handler)
    _run(server.stormsense_list_transfers(status="PENDING", urgency=None))
    assert seen["url"].endswith("/api/transfers?status=PENDING")


def test_bad_transfer_id_never_reaches_the_api():
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - must not run
        raise AssertionError("the API should not be called for a bad id")

    _api(handler)
    result = _run(server.stormsense_get_transfer("../overview"))
    assert result["ok"] is False


def test_api_error_message_is_returned_to_the_client():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"detail": {"code": "read_only", "message": "Your account can view transfers but not approve or reject them."}})

    _api(handler)
    result = _run(server.stormsense_approve_transfers(ids=["TR-0ABC123456"]))
    assert result == {"ok": False, "status": 403, "error": "Your account can view transfers but not approve or reject them."}


def test_unreachable_api_is_reported_not_raised():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    _api(handler)
    result = _run(server.stormsense_overview())
    assert result["ok"] is False and "not reachable" in result["error"]


def test_writes_send_the_same_origin_header():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["header"] = request.headers["x-requested-with"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"action": "APPROVED", "changed": ["TR-0ABC123456"], "skipped": [], "message": "ok"})

    _api(handler)
    _run(server.stormsense_approve_transfers(ids=["TR-0ABC123456"], note="from MCP"))
    assert seen["header"] == "stormsense"
    assert seen["body"] == {"ids": ["TR-0ABC123456"], "note": "from MCP"}
