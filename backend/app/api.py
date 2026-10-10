"""HTTP endpoints. Thin: validation and permissions here, meaning in service.py."""
from __future__ import annotations

import csv
import io
import logging
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .agent import StormDesk
from .alerts import JobMissing, start_demo_email
from .auth import current_user, get_service, is_live, planner, problem, requested_source, same_origin
from .dbx import WarmingUp
from .schemas import (
    ApproveRequest,
    AskRequest,
    AskResponse,
    BacktestStorm,
    ChangeSince,
    DecisionResult,
    DemoAlertResult,
    Health,
    Impact,
    ImpactHeadline,
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
    TimelineEvent,
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
def approve(body: ApproveRequest, request: Request, user: Annotated[Me, Depends(planner)], svc: Svc) -> DecisionResult:
    result = svc.decide("APPROVED", body.ids, user.email, body.note)
    log_event(request, "transfers_approved", user.name, count=len(result.changed))
    return result


@router.post("/transfers/reject", response_model=DecisionResult, tags=["transfers"], dependencies=[Depends(same_origin)])
def reject(body: RejectRequest, request: Request, user: Annotated[Me, Depends(planner)], svc: Svc) -> DecisionResult:
    result = svc.decide("REJECTED", body.ids, user.email, body.reason, body.reason_code)
    log_event(request, "transfers_rejected", user.name, count=len(result.changed))
    return result


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


class MarkdownDecision(BaseModel):
    store_id: str = Field(pattern=r"^S\d{2}$")
    product_id: str = Field(pattern=r"^P\d{2}$")
    decision: Literal["APPROVED", "REJECTED"]


@router.post("/markdowns/decision", response_model=MarkdownSuggestion, tags=["stores"], dependencies=[Depends(same_origin)])
def decide_markdown(body: MarkdownDecision, request: Request, user: Annotated[Me, Depends(planner)], svc: Svc) -> MarkdownSuggestion:
    """A planner approves or rejects a markdown suggestion. Records the decision; nothing changes in the stores."""
    found = svc.decide_markdown(body.store_id, body.product_id, body.decision, user.name)
    if found is None:
        raise problem(404, "not_found", "That markdown suggestion is no longer on the list.")
    log_event(request, "markdown_decided", user.name, decision=body.decision)
    return found


def log_event(request: Request, kind: str, actor: str, **detail: Any) -> None:
    """Writes to the event log that feeds the business impact timeline. Only on a copy with uploads switched on."""
    settings = request.app.state.settings
    if settings.ingest_enabled:
        from .events import record

        record(settings.ingest_dir, kind, actor, **detail)


@router.get("/analysis/charts", tags=["analysis"])
def analysis_charts(user: User, svc: Svc) -> dict[str, Any]:
    """Demand, stock, shortages, transfers and protected sales, for the chosen data source."""
    return svc.analysis_charts()


@router.get("/impact", response_model=Impact, tags=["impact"])
def impact(request: Request, user: User, svc: Svc) -> Impact:
    """What the plan is worth: protected sales, estimated profit and carbon, the decisions made, and the timeline of updates."""
    from .events import read
    from .ingest import IngestStore
    from .ingest_plan import DEFAULT_ECONOMICS, economics, net_benefit

    settings = request.app.state.settings
    figures = svc.impact_figures()
    econ = economics(IngestStore(settings.ingest_dir)) if settings.ingest_enabled else dict(DEFAULT_ECONOMICS)
    money = net_benefit({"protected_usd": figures["protected_usd"], "miles": figures["miles"]}, econ)
    events = read(settings.ingest_dir, 40) if settings.ingest_enabled else []
    plans = [e for e in events if e["kind"] == "plan_built"]
    last_plan = plans[0] if plans else None
    return Impact(
        source=requested_source(request), as_of=figures["as_of"],
        headline=ImpactHeadline(protected_usd=figures["protected_usd"], margin_usd=money["margin_usd"],
                                trucking_usd=money["trucking_usd"], net_usd=money["net_usd"], co2_kg=figures["co2_kg"],
                                moves=figures["moves"], pending=figures["pending"], approved=figures["approved"],
                                rejected=figures["rejected"]),
        assumptions=[f"Margin on sales is {econ['margin_pct']:g}% (your figure, or the default).",
                     f"Trucking is ${econ['truck_cost_per_mile']:g} per mile, one truck trip per move.",
                     "Carbon is about 0.9 kg CO2e per loaded truck-mile, with 200 units to a truck.",
                     "Protected sales are gross revenue, not profit, and use the forecast, not what really sold."],
        changes=ChangeSince(last_plan_at=last_plan["at"] if last_plan else None,
                            moves_then=last_plan.get("transfers") if last_plan else None, moves_now=figures["pending"]),
        timeline=[TimelineEvent(at=e["at"], kind=e["kind"], actor=e["actor"], detail=describe(e)) for e in events],
    )


def describe(e: dict[str, Any]) -> str:
    """One plain sentence for a timeline entry."""
    kind = e["kind"]
    if kind == "upload":
        return f"Uploaded {e.get('feed', 'a file')}: {e.get('kept', 0)} rows kept, {e.get('refused', 0)} refused."
    if kind == "demo_loaded":
        return "Loaded the sample workbooks."
    if kind == "plan_built":
        return f"Built the plan: {e.get('transfers', 0)} moves, {e.get('short', 0)} products short."
    if kind == "economics_saved":
        return f"Changed the cost inputs: ${e.get('truck_cost_per_mile', 0):g} per mile, {e.get('margin_pct', 0):g}% margin."
    if kind == "drop_loaded":
        return f"Loaded from the drop folder: {', '.join(e.get('feeds', []))}."
    if kind == "transfers_approved":
        return f"Approved {e.get('count', 0)} move{'s' if e.get('count', 0) != 1 else ''}."
    if kind == "transfers_rejected":
        return f"Rejected {e.get('count', 0)} move{'s' if e.get('count', 0) != 1 else ''}."
    if kind == "markdown_decided":
        return f"{'Approved' if e.get('decision') == 'APPROVED' else 'Rejected'} a markdown."
    return kind.replace("_", " ").capitalize()


class Briefing(BaseModel):
    headline: str
    lines: list[str]


@router.get("/briefing", response_model=Briefing, tags=["today"])
def briefing(user: User, svc: Svc) -> Briefing:
    """The morning briefing: a few plain sentences from today's figures, for the chosen data source."""
    from .briefing import build

    data = build(svc.overview(), svc.stores(), svc.transfers("PENDING", None), svc.markdowns("live"))
    return Briefing(**data)


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
def storm_desk(body: StormDeskRequest, request: Request, user: User, svc: Svc) -> StormDeskPlan:
    """Plans from the live data. Read-only: it can suggest moves but never approves or changes anything."""
    if not request.app.state.desk_limiter.allow(user.email):
        raise problem(429, "slow_down", "Storm desk has been asked a lot. Wait a minute, then try again.", **{"Retry-After": "60"})
    desk: StormDesk | None = request.app.state.storm_desk
    if desk is None or not is_live(request):
        return StormDeskPlan(answered=False, message="Storm desk needs the live workspace. It isn't available with sample data.")
    result = desk.run(body.goal.strip())
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
    if scorer is None or not is_live(request):
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
