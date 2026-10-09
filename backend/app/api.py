"""HTTP endpoints. Thin: validation and permissions here, meaning in service.py."""
from __future__ import annotations

import csv
import io
import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import Response

from .agent import StormDesk
from .alerts import JobMissing, start_demo_email
from .auth import current_user, get_service, planner, problem, same_origin
from .dbx import WarmingUp
from .schemas import (
    ApproveRequest,
    AskRequest,
    AskResponse,
    BacktestStorm,
    DecisionResult,
    DemoAlertResult,
    Health,
    InventoryItem,
    MarkdownSuggestion,
    Me,
    Overview,
    PlanChange,
    RejectRequest,
    StoreForecast,
    StoreSummary,
    StormDeskPlan,
    StormDeskRequest,
    Transfer,
    WhatIfRequest,
    WhatIfResult,
    WhatIfRow,
)
from .service import Service
from .whatif import Scenario
from .whatif import run as run_what_if

router = APIRouter(prefix="/api")
log = logging.getLogger("stormsense.api")
Svc = Annotated[Service, Depends(get_service)]
# live = the real forecast; demo = a demo storm placed on the Florida stores, for showing what a storm would look like
WeatherMode = Annotated[Literal["live", "demo"], Query()]
User = Annotated[Me, Depends(current_user)]


@router.get("/health", response_model=Health, tags=["system"])
def health(request: Request, svc: Svc, deep: bool = False) -> Health:
    """Liveness. With ?deep=true it also checks the data connection (this wakes the warehouse, so keep probes sparse)."""
    mode, warehouse = request.app.state.settings.mode, "not_checked"
    if deep:
        try:
            svc.source.ping()
            warehouse = "ready"
        except WarmingUp:
            warehouse = "starting"
        except Exception:  # noqa: BLE001 - any failure means the data connection is not usable
            warehouse = "unavailable"
    status = {"ready": "ok", "not_checked": "ok", "starting": "starting", "unavailable": "unavailable"}[warehouse]
    return Health(status=status, mode=mode, warehouse=warehouse)  # type: ignore[arg-type]


@router.get("/me", response_model=Me, tags=["people"])
def me(user: User) -> Me:
    return user


@router.get("/overview", response_model=Overview, tags=["today"])
def overview(user: User, svc: Svc, weather: WeatherMode = "live") -> Overview:
    return svc.overview(weather)


@router.get("/transfers", response_model=list[Transfer], tags=["transfers"])
def transfers(user: User, svc: Svc, status: Literal["PENDING", "APPROVED", "REJECTED"] | None = None,
              urgency: Literal["URGENT", "NORMAL"] | None = None) -> list[Transfer]:
    return svc.transfers(status, urgency)


@router.post("/transfers/approve", response_model=DecisionResult, tags=["transfers"], dependencies=[Depends(same_origin)])
def approve(body: ApproveRequest, user: Annotated[Me, Depends(planner)], svc: Svc) -> DecisionResult:
    return svc.decide("APPROVED", body.ids, user.email, body.note)


@router.post("/transfers/reject", response_model=DecisionResult, tags=["transfers"], dependencies=[Depends(same_origin)])
def reject(body: RejectRequest, user: Annotated[Me, Depends(planner)], svc: Svc) -> DecisionResult:
    return svc.decide("REJECTED", body.ids, user.email, body.reason, body.reason_code)


EXPORT_COLUMNS = ["Transfer id", "Status", "Urgency", "Product", "Quantity", "From store", "To store",
                  "Distance (miles)", "Sales protected (USD)", "Estimated kg CO2e", "Reason", "Decided by", "Decided at", "Note"]


def _cell(value: object) -> str:
    """Spreadsheets run a cell that starts with = + - or @ as a formula; keep planner text as plain text."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


@router.get("/transfers/export", tags=["transfers"], response_class=Response)
def export_transfers(user: User, svc: Svc, status: Literal["PENDING", "APPROVED", "REJECTED"] | None = None) -> Response:
    """The plan as a spreadsheet (CSV). Read-only. Open it in a spreadsheet, or print it to PDF from the browser."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(EXPORT_COLUMNS)
    for t in svc.transfers(status, None):
        writer.writerow([_cell(v) for v in [
            t.id, t.status, t.urgency, t.product.name, t.qty, t.from_store.name, t.to_store.name, t.distance_miles,
            round(t.sales_protected_usd), t.co2_kg, t.reason, t.decided_by, t.decided_at.isoformat() if t.decided_at else "", t.note,
        ]])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="stormsense-plan.csv"'})


@router.get("/markdowns", response_model=list[MarkdownSuggestion], tags=["stores"])
def markdowns(user: User, svc: Svc, weather: WeatherMode = "live") -> list[MarkdownSuggestion]:
    """Surplus stock that would not sell in time at full price, with a discount that adds cash. Suggestions only: nothing changes."""
    return svc.markdowns(weather)


@router.post("/demo/alert", response_model=DemoAlertResult, tags=["demo"], dependencies=[Depends(same_origin)])
def demo_alert(request: Request, user: Annotated[Me, Depends(planner)]) -> DemoAlertResult:
    """Starts the demo email job. Databricks sends the email to the alert address. Planners only."""
    if not request.app.state.alert_limiter.allow(user.email):
        raise problem(429, "slow_down", "A demo email was just started. Wait a minute, then try again.", **{"Retry-After": "60"})
    workspace = request.app.state.workspace
    if workspace is None:
        raise problem(409, "not_configured", "The demo email needs the live workspace. It isn't available with sample data.")
    try:
        start_demo_email(workspace, request.app.state.settings.demo_job_name)
    except JobMissing:
        raise problem(409, "not_configured", "The demo email job isn't in the workspace yet. Deploy the bundle first.") from None
    except Exception:  # noqa: BLE001 - the workspace may refuse; the reason stays in the server log, not the browser
        log.exception("demo email job could not be started")
        raise problem(502, "job_failed", "The email could not be started. Try again in a minute.") from None
    return DemoAlertResult(started=True, message="Started. Databricks sends the email within a few minutes.")


@router.get("/backtest", response_model=list[BacktestStorm], tags=["history"])
def backtest(user: User, svc: Svc) -> list[BacktestStorm]:
    """Past storms replayed with what really sold: the sales lost, and how much nearby stock could have covered.

    An upper bound, not a forecast.
    """
    return svc.backtest()


@router.get("/transfers/{transfer_id}", response_model=Transfer, tags=["transfers"])
def transfer(transfer_id: Annotated[str, Path(pattern=r"^TR-[A-Z0-9]{10}$")], user: User, svc: Svc) -> Transfer:
    found = svc.transfer(transfer_id)
    if not found:
        raise problem(404, "not_found", "We couldn't find that transfer.")
    return found


@router.get("/stores", response_model=list[StoreSummary], tags=["stores"])
def stores(user: User, svc: Svc, weather: WeatherMode = "live") -> list[StoreSummary]:
    return svc.stores(weather)


@router.get("/stores/{store_id}/forecast", response_model=StoreForecast, tags=["stores"])
def store_forecast(store_id: Annotated[str, Path(pattern=r"^S\d{2}$")], user: User, svc: Svc,
                   weather: WeatherMode = "live") -> StoreForecast:
    found = svc.store_forecast(store_id, weather)
    if not found:
        raise problem(404, "not_found", "We couldn't find that store.")
    return found


@router.get("/inventory", response_model=list[InventoryItem], tags=["stores"])
def inventory(user: User, svc: Svc, status: Literal["RUNNING_LOW", "EXTRA"] | None = Query(None)) -> list[InventoryItem]:
    return svc.inventory(status)


@router.get("/history", response_model=list[Transfer], tags=["transfers"])
def history(user: User, svc: Svc) -> list[Transfer]:
    return svc.history()


@router.post("/ask", response_model=AskResponse, tags=["ask"], dependencies=[Depends(same_origin)])
def ask(body: AskRequest, request: Request, user: User, svc: Svc) -> AskResponse:
    if not request.app.state.limiter.allow(user.email):
        raise problem(429, "slow_down", "You're asking quickly. Wait a moment, then try again.", **{"Retry-After": "30"})
    return svc.ask(body.question.strip())


@router.post("/storm-desk", response_model=StormDeskPlan, tags=["storm desk"], dependencies=[Depends(same_origin)])
def storm_desk(body: StormDeskRequest, request: Request, user: User) -> StormDeskPlan:
    """Plans from the live data. Read-only: it can suggest moves but never approves or changes anything."""
    if not request.app.state.desk_limiter.allow(user.email):
        raise problem(429, "slow_down", "Storm desk has been asked a lot. Wait a minute, then try again.", **{"Retry-After": "60"})
    desk: StormDesk | None = request.app.state.storm_desk
    if desk is None:
        return StormDeskPlan(answered=False, message="Storm desk needs the live workspace. It isn't available with sample data.")
    result = desk.run(body.goal.strip())
    svc: Service = request.app.state.service
    transfers = [t for t in (svc.transfer(i) for i in result.transfer_ids) if t and t.status == "PENDING"]
    return StormDeskPlan(
        answered=result.answered, plan=result.plan, message=result.message, transfers=transfers,
        steps=[{"what": s.tool.replace("get_", "").replace("_", " ").capitalize(), "result": s.detail} for s in result.steps],
        debate=[{"agent": d.agent, "message": d.message} for d in result.debate],
    )


@router.post("/what-if", response_model=WhatIfResult, tags=["what-if"], dependencies=[Depends(same_origin)])
def what_if(body: WhatIfRequest, request: Request, user: User, svc: Svc) -> WhatIfResult:
    """Simulates a storm and what it would cost. Read-only: it changes no data and approves nothing."""
    import pandas as pd

    if not request.app.state.what_if_limiter.allow(user.email):
        raise problem(429, "slow_down", "That's a lot of simulations. Wait a minute, then try again.", **{"Retry-After": "60"})
    scorer = request.app.state.forecast_scorer
    if scorer is None:
        return WhatIfResult(answered=False, message="The storm simulator needs the live workspace. It isn't available with sample data.")
    source = svc.source
    rows = source.forecast_inputs(body.region)
    if not rows:
        return WhatIfResult(answered=False, message="There is no forecast for the coming days to simulate.")
    frame = pd.DataFrame(rows)
    gaps = source.gaps(None, None)
    as_of = max(g["as_of_date"] for g in gaps)
    available = {(g["store_id"], g["product_id"]): float(g["available"] or 0) for g in gaps}
    names = {s.id: s.name for s in svc.stores()} | {p["product_id"]: p["name"] for p in source.products()}
    prices = {p["product_id"]: float(p["unit_price"]) for p in source.products()}
    sc = Scenario(strength=body.strength, start_day=body.start_day, days=body.days, region=body.region)
    result = run_what_if(frame, sc, as_of, scorer, available, prices, names)
    change = source.stock_plan_change()
    window = result["window"]
    sentence = (f"A storm of strength {body.strength} from {window} would add about {result['extra_demand_units']} units of demand. "
                f"Without moving stock, about ${result['extra_lost_usd']:,.0f} in sales would be lost. "
                f"Moving about {result['stock_to_move_units']} units of stock would cover it.")
    plan_change = None
    if change:
        b, n = change["before"], change["now"]
        plan_change = PlanChange(
            as_of=change["as_of"], before_version=change["before_version"], before_time=change["before_time"],
            now_version=change["now_version"], now_time=change["now_time"],
            shortage_stores_before=b["shortage_stores"], shortage_stores_now=n["shortage_stores"],
            units_short_before=b["units_short"], units_short_now=n["units_short"],
            sentence=(f"The stock plan changed after the last daily run: {n['shortage_stores']} stores now show a shortage, "
                      f"compared with {b['shortage_stores']} before it."),
        )
    return WhatIfResult(answered=True, window=window, sentence=sentence, normal_units=result["normal_units"],
                        storm_units=result["storm_units"], extra_demand_units=result["extra_demand_units"],
                        extra_lost_usd=result["extra_lost_usd"], stock_to_move_units=result["stock_to_move_units"],
                        rows=[WhatIfRow(**r) for r in result["rows"]], plan_change=plan_change)
