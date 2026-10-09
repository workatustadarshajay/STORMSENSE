"""StormSense MCP server.

Exposes the StormSense API as MCP tools (Model Context Protocol, Streamable HTTP),
so any MCP-capable assistant, agent framework or app can read the storm plan,
ask questions, run a what-if, and approve or reject transfers.

The server holds no data and no database connection. Every call goes through the
StormSense API, so its roles, rate limits and read-only rules still apply.

Run:
    STORMSENSE_API_URL=http://localhost:8000/api uv run uvicorn server:app --port 8200
"""

from __future__ import annotations

import json
import os
import re
from typing import Literal

import httpx
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

API_URL = os.environ.get("STORMSENSE_API_URL", "http://localhost:8000/api").rstrip("/")
# Whose authority the calls use. The API trusts this header only behind its own sign-in proxy,
# so point this at a planner account on local or test setups only.
PLANNER_EMAIL = os.environ.get("STORMSENSE_MCP_USER", "ava.planner@stormsense.test")
# Storm desk and the what-if can take a while, especially when the warehouse is waking up.
TIMEOUT = 120
# Tests replace this with an in-process transport. Leave it None in normal runs.
TRANSPORT: httpx.AsyncBaseTransport | None = None

TRANSFER_ID = re.compile(r"^TR-[A-Z0-9]{10}$")
STORE_ID = re.compile(r"^S\d{2}$")

mcp = FastMCP("stormsense_mcp")


def _out(data: object) -> str:
    return json.dumps(data, indent=2, default=str)


def _bad_id(value: str, pattern: re.Pattern[str], label: str) -> str | None:
    if pattern.fullmatch(value):
        return None
    return _out({"ok": False, "error": f"That isn't a valid {label}."})


async def _call(method: str, path: str, body: dict | None = None, params: dict | None = None) -> str:
    """One StormSense API call, returned as JSON text. Errors come back as {"ok": false, "error": ...}."""
    headers = {"X-Forwarded-Email": PLANNER_EMAIL, "X-Requested-With": "stormsense"}
    clean_params = {k: v for k, v in (params or {}).items() if v is not None} or None
    try:
        async with httpx.AsyncClient(base_url=API_URL, timeout=TIMEOUT, headers=headers, transport=TRANSPORT) as http:
            resp = await http.request(method, path, json=body, params=clean_params)
    except httpx.HTTPError as e:
        return _out({"ok": False, "error": f"StormSense API is not reachable ({type(e).__name__})."})
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail")
        except ValueError:
            detail = None
        message = detail.get("message") if isinstance(detail, dict) else None
        return _out({"ok": False, "status": resp.status_code, "error": message or f"StormSense API returned {resp.status_code}."})
    return _out(resp.json())


READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
WRITES = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


# --------------------------------------------------------------------------- read tools


@mcp.tool(name="stormsense_overview", annotations={"title": "Today's storm overview", **READ_ONLY})
async def stormsense_overview() -> str:
    """Summarise today: urgent transfers, transfers waiting, stores at risk, and the next weather alert.

    Returns:
        str: JSON with urgent_transfers, pending_transfers, stores_at_risk, alerts and next_action.
    """
    return await _call("GET", "/overview")


@mcp.tool(name="stormsense_list_transfers", annotations={"title": "List transfer recommendations", **READ_ONLY})
async def stormsense_list_transfers(
    status: Literal["PENDING", "APPROVED", "REJECTED"] | None = "PENDING",
    urgency: Literal["URGENT", "NORMAL"] | None = None,
) -> str:
    """List stock transfers between stores, newest first. Defaults to transfers still waiting for a decision.

    Args:
        status: PENDING, APPROVED or REJECTED. Omit for all.
        urgency: URGENT or NORMAL. Omit for both.

    Returns:
        str: JSON list of transfers, each with id, headline, product, from_store, to_store, qty,
        urgency, reason, sales_protected_usd and status.
    """
    return await _call("GET", "/transfers", params={"status": status, "urgency": urgency})


@mcp.tool(name="stormsense_get_transfer", annotations={"title": "Get one transfer", **READ_ONLY})
async def stormsense_get_transfer(transfer_id: str) -> str:
    """Get one transfer by id (for example TR-0ABC123456), with its reason and decision history.

    Args:
        transfer_id: The transfer id, starting with TR-.

    Returns:
        str: JSON transfer object, or an error if the id is unknown.
    """
    if error := _bad_id(transfer_id, TRANSFER_ID, "transfer id"):
        return error
    return await _call("GET", f"/transfers/{transfer_id}")


@mcp.tool(name="stormsense_list_stores", annotations={"title": "List stores", **READ_ONLY})
async def stormsense_list_stores() -> str:
    """List the stores in the network (id and name). Use the id with stormsense_store_forecast.

    Returns:
        str: JSON list of {"id": "S01", "name": str}.
    """
    return await _call("GET", "/stores")


@mcp.tool(name="stormsense_store_forecast", annotations={"title": "Store demand forecast", **READ_ONLY})
async def stormsense_store_forecast(store_id: str) -> str:
    """Get a store's demand forecast for the next seven days, by product, with the weather behind it.

    Args:
        store_id: The store id, for example S01.

    Returns:
        str: JSON forecast for the store, or an error if the store is unknown.
    """
    if error := _bad_id(store_id, STORE_ID, "store id"):
        return error
    return await _call("GET", f"/stores/{store_id}/forecast")


@mcp.tool(name="stormsense_ask", annotations={"title": "Ask StormSense a question", **READ_ONLY})
async def stormsense_ask(question: str) -> str:
    """Ask a plain-English question about stock, sales or the forecast. Answered from the live data.

    Args:
        question: The question, for example "Which stores run low this week?".

    Returns:
        str: JSON with a one-sentence answer and optional table.
    """
    return await _call("POST", "/ask", body={"question": question})


@mcp.tool(name="stormsense_what_if", annotations={"title": "Simulate a storm", **READ_ONLY})
async def stormsense_what_if(
    strength: int,
    start_day: int = 0,
    days: int = 2,
    region: Literal["Florida", "Texas", "California"] | None = None,
) -> str:
    """Simulate a storm and estimate the sales lost if nothing moves. Changes no data.

    Args:
        strength: How strong the storm is, 0 to 100.
        start_day: When it hits. 0 means tomorrow, up to 6.
        days: How many days it lasts, 1 to 4.
        region: Florida, Texas or California. Omit for the whole network.

    Returns:
        str: JSON with normal and storm units, sales lost, and the stock that would need to move.
    """
    body = {"strength": strength, "start_day": start_day, "days": days, "region": region}
    return await _call("POST", "/what-if", body=body)


@mcp.tool(name="stormsense_storm_desk_plan", annotations={"title": "Ask storm desk for a plan", **READ_ONLY})
async def stormsense_storm_desk_plan(goal: str) -> str:
    """Ask the storm desk crew for a plan for a goal, for example "Prepare Florida for Sunday's storm".

    The crew checks the live data and names only real pending transfers. It takes about a minute.
    It does not approve or change anything.

    Args:
        goal: What to prepare for, in plain words.

    Returns:
        str: JSON with the plan, the transfers it refers to, and the checks it made.
    """
    return await _call("POST", "/storm-desk", body={"goal": goal})


# --------------------------------------------------------------------------- write tools


@mcp.tool(name="stormsense_approve_transfers", annotations={"title": "Approve transfers", **WRITES})
async def stormsense_approve_transfers(ids: list[str], note: str | None = None) -> str:
    """Approve pending transfers so the stock moves. Needs a planner account; the API checks it.

    Args:
        ids: Transfer ids to approve, up to 50.
        note: Optional note for the audit trail, up to 280 characters.

    Returns:
        str: JSON with the transfers changed and any skipped, or an error.
    """
    if error := next((_bad_id(i, TRANSFER_ID, "transfer id") for i in ids if not TRANSFER_ID.fullmatch(i)), None):
        return error
    return await _call("POST", "/transfers/approve", body={"ids": ids, "note": note})


@mcp.tool(name="stormsense_reject_transfers", annotations={"title": "Reject transfers", **WRITES})
async def stormsense_reject_transfers(
    ids: list[str],
    reason: str,
    reason_code: Literal["TRUCK_UNAVAILABLE", "STORE_CLOSED", "ALREADY_COVERED", "ROUTE_TOO_SLOW", "OTHER"] | None = None,
) -> str:
    """Reject pending transfers with a reason. The next daily run learns from the reason.

    Args:
        ids: Transfer ids to reject, up to 50.
        reason: Why, in plain words (3 to 280 characters).
        reason_code: A structured reason. The daily run learns from it.

    Returns:
        str: JSON with the transfers changed and any skipped, or an error.
    """
    if error := next((_bad_id(i, TRANSFER_ID, "transfer id") for i in ids if not TRANSFER_ID.fullmatch(i)), None):
        return error
    body = {"ids": ids, "reason": reason, "reason_code": reason_code}
    return await _call("POST", "/transfers/reject", body=body)


# --------------------------------------------------------------------------- ASGI app
# uvicorn target: `uvicorn server:app --port 8200`. MCP at /mcp, health at /health.
# custom_route keeps /health in the same app whose lifespan runs the Streamable HTTP session manager.


@mcp.custom_route("/health", methods=["GET"])
async def health(request) -> JSONResponse:
    """Liveness probe for the MCP service."""
    return JSONResponse(
        {"service": "stormsense-mcp", "version": "1.0.0", "transport": "streamable-http", "endpoint": "/mcp", "tools": 10}
    )


app = mcp.streamable_http_app()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8200)
