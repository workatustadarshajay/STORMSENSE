"""The API contract. The frontend's TypeScript types are generated from these models."""
from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

Role = Literal["viewer", "planner", "admin"]
Urgency = Literal["URGENT", "NORMAL"]
Confidence = Literal["High", "Medium", "Low"]
TransferStatus = Literal["PENDING", "APPROVED", "REJECTED"]
StockStatus = Literal["RUNNING_LOW", "EXTRA", "OK"]
AlertKind = Literal["storm", "heavy_rain", "heat"]

TransferId = Annotated[str, StringConstraints(pattern=r"^TR-[A-Z0-9]{10}$")]


class Me(BaseModel):
    email: str
    name: str
    role: Role
    can_approve: bool
    data_label: str | None = Field(None, description="Set to 'sample' while the app shows sample data")


class Ref(BaseModel):
    id: str
    name: str


class ProductRef(Ref):
    name_plural: str


class WeatherAlert(BaseModel):
    date: date
    weekday: str
    kind: AlertKind
    title: str
    detail: str
    stores: list[str]


class NextAction(BaseModel):
    title: str
    detail: str
    button: str
    path: str


class Overview(BaseModel):
    urgent_transfers: int
    pending_transfers: int
    stores_at_risk: int
    next_alert: WeatherAlert | None
    alerts: list[WeatherAlert]
    next_action: NextAction
    as_of: date | None


class Transfer(BaseModel):
    id: str
    headline: str
    product: ProductRef
    from_store: Ref
    to_store: Ref
    qty: int
    urgency: Urgency
    confidence: Confidence
    reason: str
    sales_protected_usd: float
    distance_miles: int
    co2_kg: float = Field(0, description="Estimated kg CO2e for the move. See carbon.py for the assumptions.")
    runs_low_day: str | None
    status: TransferStatus
    created_at: datetime | None
    decided_by: str | None = None
    decided_at: datetime | None = None
    note: str | None = None


class ApproveRequest(BaseModel):
    ids: list[TransferId] = Field(min_length=1, max_length=50)
    note: str | None = Field(None, max_length=280)


RejectReason = Literal["TRUCK_UNAVAILABLE", "STORE_CLOSED", "ALREADY_COVERED", "ROUTE_TOO_SLOW", "OTHER"]


class RejectRequest(BaseModel):
    ids: list[TransferId] = Field(min_length=1, max_length=50)
    reason: str = Field(min_length=3, max_length=280)
    reason_code: RejectReason | None = Field(None, description="Structured reason; the daily run learns from it")


class DecisionResult(BaseModel):
    action: Literal["APPROVED", "REJECTED"]
    changed: list[str]
    skipped: list[str]
    message: str


class StoreSummary(Ref):
    city: str
    region: str
    running_low: int


class DayUnits(BaseModel):
    date: date
    weekday: str
    units: int


class WeatherDay(BaseModel):
    date: date
    weekday: str
    condition: str
    label: str
    temp_max_f: int
    wind_max_mph: int
    rain_in: float


class ProductForecast(BaseModel):
    product: ProductRef
    days: list[DayUnits]
    total_units: int
    range_low: int
    range_high: int
    available: int
    status: StockStatus
    runs_low_day: str | None
    why: str


class StoreForecast(BaseModel):
    store: StoreSummary
    weather: list[WeatherDay]
    products: list[ProductForecast]
    as_of: date | None


class InventoryItem(BaseModel):
    store: Ref
    product: ProductRef
    status: StockStatus
    available: int
    on_the_way: int
    days_of_cover: float | None
    runs_low_day: str | None
    spare_units: int


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AskTable(BaseModel):
    columns: list[str]
    rows: list[list[str | int | float | None]]


class AskResponse(BaseModel):
    answered: bool
    answer: str
    table: AskTable | None = None


class Health(BaseModel):
    status: Literal["ok", "starting", "unavailable"]
    mode: str
    warehouse: Literal["ready", "starting", "unavailable", "not_checked"]


class StormDeskRequest(BaseModel):
    goal: str = Field(min_length=3, max_length=500)


class DeskStep(BaseModel):
    what: str = Field(description="Plain-language description of what storm desk checked")
    result: str


class DebateTurn(BaseModel):
    agent: str = Field(description="Which role spoke: Forecaster, Risk checker or Summary writer")
    message: str


class StormDeskPlan(BaseModel):
    answered: bool
    plan: list[str] = Field(default_factory=list, description="The plan, one sentence per item")
    steps: list[DeskStep] = Field(default_factory=list, description="What storm desk checked, in order")
    debate: list[DebateTurn] = Field(default_factory=list, description="How the three roles arrived at the plan")
    transfers: list[Transfer] = Field(default_factory=list, description="Pending transfers the plan refers to")
    message: str | None = None


StormDeskPlan.model_rebuild()


class WhatIfRequest(BaseModel):
    strength: int = Field(ge=0, le=100, description="How strong the storm is, 0 to 100")
    start_day: int = Field(ge=0, le=6, description="0 means tomorrow")
    days: int = Field(ge=1, le=4, description="How many days the storm lasts")
    region: Literal["Florida", "Texas", "California"] | None = None


class WhatIfRow(BaseModel):
    store: str
    product: str
    normal_units: int
    storm_units: int
    on_hand: int
    extra_lost_usd: float


class PlanChange(BaseModel):
    as_of: str
    before_version: int
    before_time: str
    now_version: int
    now_time: str
    shortage_stores_before: int
    shortage_stores_now: int
    units_short_before: int
    units_short_now: int
    sentence: str


class WhatIfResult(BaseModel):
    answered: bool
    message: str | None = None
    window: str | None = None
    sentence: str | None = None
    normal_units: int = 0
    storm_units: int = 0
    extra_demand_units: int = 0
    extra_lost_usd: float = 0.0
    stock_to_move_units: int = 0
    rows: list[WhatIfRow] = Field(default_factory=list)
    plan_change: PlanChange | None = None
