"""HTTP endpoints. Thin: validation and permissions here, meaning in service.py."""
from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query, Request

from .auth import current_user, get_service, planner, problem, same_origin
from .dbx import WarmingUp
from .schemas import (
    ApproveRequest,
    AskRequest,
    AskResponse,
    DecisionResult,
    Health,
    InventoryItem,
    Me,
    Overview,
    RejectRequest,
    StoreForecast,
    StoreSummary,
    Transfer,
)
from .service import Service

router = APIRouter(prefix="/api")
Svc = Annotated[Service, Depends(get_service)]
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
def overview(user: User, svc: Svc) -> Overview:
    return svc.overview()


@router.get("/transfers", response_model=list[Transfer], tags=["transfers"])
def transfers(user: User, svc: Svc, status: Literal["PENDING", "APPROVED", "REJECTED"] | None = None,
              urgency: Literal["URGENT", "NORMAL"] | None = None) -> list[Transfer]:
    return svc.transfers(status, urgency)


@router.post("/transfers/approve", response_model=DecisionResult, tags=["transfers"], dependencies=[Depends(same_origin)])
def approve(body: ApproveRequest, user: Annotated[Me, Depends(planner)], svc: Svc) -> DecisionResult:
    return svc.decide("APPROVED", body.ids, user.email, body.note)


@router.post("/transfers/reject", response_model=DecisionResult, tags=["transfers"], dependencies=[Depends(same_origin)])
def reject(body: RejectRequest, user: Annotated[Me, Depends(planner)], svc: Svc) -> DecisionResult:
    return svc.decide("REJECTED", body.ids, user.email, body.reason)


@router.get("/transfers/{transfer_id}", response_model=Transfer, tags=["transfers"])
def transfer(transfer_id: Annotated[str, Path(pattern=r"^TR-[A-Z0-9]{10}$")], user: User, svc: Svc) -> Transfer:
    found = svc.transfer(transfer_id)
    if not found:
        raise problem(404, "not_found", "We couldn't find that transfer.")
    return found


@router.get("/stores", response_model=list[StoreSummary], tags=["stores"])
def stores(user: User, svc: Svc) -> list[StoreSummary]:
    return svc.stores()


@router.get("/stores/{store_id}/forecast", response_model=StoreForecast, tags=["stores"])
def store_forecast(store_id: Annotated[str, Path(pattern=r"^S\d{2}$")], user: User, svc: Svc) -> StoreForecast:
    found = svc.store_forecast(store_id)
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
