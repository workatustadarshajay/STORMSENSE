"""Turns raw rows into what planners see: names instead of ids, sentences instead of codes."""
from __future__ import annotations

import re
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from datetime import date
from typing import Any, TypeVar

from .carbon import estimate_kg_co2e
from .config import Settings
from .schemas import (
    AskResponse,
    AskTable,
    DayUnits,
    DecisionResult,
    InventoryItem,
    Me,
    NextAction,
    Overview,
    ProductForecast,
    ProductRef,
    Ref,
    StoreForecast,
    StoreSummary,
    Transfer,
    WeatherAlert,
    WeatherDay,
)
from .sources.base import DataSource, Row

T = TypeVar("T")

KIND_LABEL = {"storm": "Storm", "heavy_rain": "Heavy rain", "heat": "Heat wave"}
SEVERITY = ["storm", "heavy_rain", "heat"]
CONDITION_LABEL = {**KIND_LABEL, "rain": "Rain", "clear": "Clear"}
STATUS = {"SHORTAGE": "RUNNING_LOW", "SURPLUS": "EXTRA", "BALANCED": "OK"}
# Planners never see these words, whatever a source returns.
BANNED = re.compile(r"\b(sql|delta|databricks|genie|mlflow|warehouse|sku|mape|wape|model|api)\b", re.I)


def weekday(d: date | None) -> str | None:
    return d.strftime("%A") if d else None


def join_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def decision_message(action: str, changed: list[str], skipped: list[str]) -> str:
    verb = "approved" if action == "APPROVED" else "rejected"
    parts = []
    if changed:
        parts.append(f"{plural(len(changed), 'transfer')} {verb}.")
    if skipped:
        parts.append(f"{len(skipped)} {'was' if len(skipped) == 1 else 'were'} already handled by someone else.")
    return " ".join(parts) or "Nothing to change."


class Service:
    def __init__(self, source: DataSource, settings: Settings) -> None:
        self.source, self.settings = source, settings
        self._cache: dict[str, tuple[float, Any]] = {}

    # ---- tiny in-memory cache for read-only data ----------------------------------------------
    def _cached(self, key: str, fn: Callable[[], T], ttl: float | None = None) -> T:
        hit = self._cache.get(key)
        if hit and hit[0] > time.monotonic():
            return hit[1]
        value = fn()
        self._cache[key] = (time.monotonic() + (self.settings.cache_seconds if ttl is None else ttl), value)
        return value

    def _directory(self) -> tuple[dict[str, Row], dict[str, Row]]:
        def load() -> tuple[dict[str, Row], dict[str, Row]]:
            return ({s["store_id"]: s for s in self.source.stores()}, {p["product_id"]: p for p in self.source.products()})
        return self._cached("directory", load, ttl=300)

    # ---- people ---------------------------------------------------------------------------
    def me(self, email: str) -> Me:
        row = self._cached(f"user:{email.lower()}", lambda: self.source.user(email), ttl=60)
        role = (row or {}).get("role") or self.settings.default_role
        name = (row or {}).get("display_name") or email.split("@")[0].replace(".", " ").title()
        label = self._cached("data_label", lambda: self.source.setting("data_label"), ttl=300)
        return Me(email=email, name=name, role=role, can_approve=role in ("planner", "admin"), data_label=label)

    # ---- transfers ------------------------------------------------------------------------
    def _transfer(self, r: Row) -> Transfer:
        stores, products = self._directory()
        p, src, dst = products[r["product_id"]], stores[r["source_store_id"]], stores[r["dest_store_id"]]
        qty = int(r["qty"])
        return Transfer(
            id=r["rec_id"],
            headline=f"Move {qty} {p['name_plural'] if qty != 1 else p['name']} from {src['name']} to {dst['name']}",
            product=ProductRef(id=p["product_id"], name=p["name"], name_plural=p["name_plural"]),
            from_store=Ref(id=src["store_id"], name=src["name"]), to_store=Ref(id=dst["store_id"], name=dst["name"]),
            qty=qty, urgency=r["urgency"], confidence=r["confidence_level"], reason=r["reason"],
            sales_protected_usd=round(float(r["sales_protected_usd"] or 0)), distance_miles=int(r["distance_miles"] or 0),
            co2_kg=estimate_kg_co2e(qty, int(r["distance_miles"] or 0)),
            runs_low_day=weekday(r.get("runs_low_date")), status=r["status"], created_at=r.get("created_at"),
            decided_by=r.get("decided_by"), decided_at=r.get("decided_at"), note=r.get("decision_note"),
        )

    def transfers(self, status: str | None, urgency: str | None) -> list[Transfer]:
        return [self._transfer(r) for r in self.source.transfers(status, urgency)]

    def transfer(self, rec_id: str) -> Transfer | None:
        r = self.source.transfer(rec_id)
        return self._transfer(r) if r else None

    def history(self) -> list[Transfer]:
        return [self._transfer(r) for r in self.source.history()]

    def decide(self, action: str, ids: list[str], actor: str, note: str | None, reason_code: str | None = None) -> DecisionResult:
        unique = list(dict.fromkeys(ids))  # a double-click or repeated id changes nothing twice
        d = self.source.decide(action, unique, actor, note, request_id=uuid.uuid4().hex, reason_code=reason_code)
        self._cache.pop("overview", None)
        return DecisionResult(action=action, changed=d.changed, skipped=d.skipped,  # type: ignore[arg-type]
                              message=decision_message(action, d.changed, d.skipped))

    # ---- today ------------------------------------------------------------------------------
    def alerts(self) -> list[WeatherAlert]:
        stores, _ = self._directory()
        groups: dict[tuple[str, str], dict[str, Any]] = {}
        for w in self.source.weather(None):
            if w["condition"] not in KIND_LABEL:
                continue
            region = stores[w["store_id"]]["region"]
            g = groups.setdefault((w["condition"], region), {"date": w["forecast_date"], "name": w.get("event_name"), "stores": {}})
            if w["forecast_date"] < g["date"]:
                g["date"], g["name"] = w["forecast_date"], w.get("event_name")
            g["stores"][stores[w["store_id"]]["name"]] = None
        out = [
            WeatherAlert(date=g["date"], weekday=weekday(g["date"]) or "", kind=kind,  # type: ignore[arg-type]
                         title=f"{g['name'] or KIND_LABEL[kind]} expected {weekday(g['date'])}",
                         detail=f"{join_names(list(g['stores']))} in {region}", stores=list(g["stores"]))
            for (kind, region), g in groups.items()
        ]
        return sorted(out, key=lambda a: (a.date, SEVERITY.index(a.kind)))[:4]

    def overview(self) -> Overview:
        def build() -> Overview:
            pending = self.source.transfers("PENDING", None)
            urgent = [r for r in pending if r["urgency"] == "URGENT"]
            shortages = self.source.gaps(None, "SHORTAGE")
            alerts = self.alerts()
            if urgent:
                protected = round(sum(float(r["sales_protected_usd"] or 0) for r in urgent), -2)
                action = NextAction(title=f"Review {plural(len(urgent), 'urgent transfer')}",
                                    detail=f"Moving this stock protects about ${protected:,.0f} in sales." if protected else
                                    "Stores are about to run low on stock.", button="Review transfers", path="/transfers")
            elif pending:
                action = NextAction(title=f"Review {plural(len(pending), 'transfer')}",
                                    detail="Nothing is urgent, but a few moves would keep shelves full.",
                                    button="Review transfers", path="/transfers")
            else:
                action = NextAction(title="You're all caught up", detail="No transfers need a decision right now.",
                                    button="See store forecasts", path="/stores")
            as_of = max((g["as_of_date"] for g in shortages), default=None) or self._as_of()
            return Overview(urgent_transfers=len(urgent), pending_transfers=len(pending),
                            stores_at_risk=len({g["store_id"] for g in shortages}), next_alert=alerts[0] if alerts else None,
                            alerts=alerts, next_action=action, as_of=as_of)
        return self._cached("overview", build)

    def _as_of(self) -> date | None:
        gaps = self.source.gaps(None, None)
        return gaps[0]["as_of_date"] if gaps else None

    # ---- stores ------------------------------------------------------------------------------
    def stores(self) -> list[StoreSummary]:
        stores, _ = self._directory()
        low: dict[str, int] = defaultdict(int)
        for g in self.source.gaps(None, "SHORTAGE"):
            low[g["store_id"]] += 1
        return [StoreSummary(id=s["store_id"], name=s["name"], city=s["city"], region=s["region"], running_low=low[s["store_id"]])
                for s in sorted(stores.values(), key=lambda s: s["name"])]

    def store_forecast(self, store_id: str) -> StoreForecast | None:
        stores, products = self._directory()
        if store_id not in stores:
            return None
        summary = next(s for s in self.stores() if s.id == store_id)
        weather = self.source.weather(store_id)
        gaps = {g["product_id"]: g for g in self.source.gaps(store_id, None)}
        by_product: dict[str, list[Row]] = defaultdict(list)
        preds = self.source.predictions(store_id)
        for r in preds:
            by_product[r["product_id"]].append(r)

        out = []
        for pid, p in products.items():
            g = gaps.get(pid)
            if not g or pid not in by_product:
                continue
            status = STATUS[g["status"]]
            out.append(ProductForecast(
                product=ProductRef(id=pid, name=p["name"], name_plural=p["name_plural"]),
                days=[DayUnits(date=r["forecast_date"], weekday=weekday(r["forecast_date"]) or "", units=round(r["predicted_units"]))
                      for r in by_product[pid]],
                total_units=round(g["forecast_units"]), range_low=round(g["forecast_p10"]), range_high=round(g["forecast_p90"]),
                available=round(g["available"]), status=status,  # type: ignore[arg-type]
                runs_low_day=weekday(g["runs_low_date"]) if status == "RUNNING_LOW" else None,
                why=self._why(p, weather, status),
            ))
        out.sort(key=lambda f: (f.status != "RUNNING_LOW", f.status != "EXTRA", f.product.id))
        days = [
            WeatherDay(date=w["forecast_date"], weekday=weekday(w["forecast_date"]) or "", condition=w["condition"],
                       label=CONDITION_LABEL.get(w["condition"], w["condition"]), temp_max_f=round(w["temp_max_f"]),
                       wind_max_mph=round(w["wind_max_mph"]), rain_in=round(w["rain_in"], 1))
            for w in weather
        ]
        as_of = preds[0]["as_of_date"] if preds else None
        return StoreForecast(store=summary, weather=days, products=out, as_of=as_of)

    @staticmethod
    def _why(product: Row, weather: list[Row], status: str) -> str:
        """The weather behind a product's week, in a sentence."""
        driver = product["weather_driver"]
        match = {"wind": ["storm"], "rain": ["storm", "heavy_rain"], "heat": ["heat"]}[driver]
        hits = [w for w in weather if w["condition"] in match]
        if hits:
            w = min(hits, key=lambda x: x["forecast_date"])
            day = weekday(w["forecast_date"])
            detail = {"wind": f"winds up to {round(max(h['wind_max_mph'] for h in hits))} mph",
                      "rain": f"about {max(h['rain_in'] for h in hits):.1f} in of rain",
                      "heat": f"highs near {round(max(h['temp_max_f'] for h in hits))}°F"}[driver]
            return f"{CONDITION_LABEL[w['condition']]} on {day}, with {detail}, is lifting demand for {product['name_plural']}."
        return "A normal week is expected here." if status != "EXTRA" else "More than enough for this week's expected sales."

    # ---- inventory -----------------------------------------------------------------------------
    def inventory(self, status: str | None) -> list[InventoryItem]:
        stores, products = self._directory()
        want = {"RUNNING_LOW": "SHORTAGE", "EXTRA": "SURPLUS"}.get(status or "")
        rows = [g for g in self.source.gaps(None, want) if g["status"] in ("SHORTAGE", "SURPLUS")]
        out = [
            InventoryItem(store=Ref(id=g["store_id"], name=stores[g["store_id"]]["name"]),
                          product=ProductRef(id=g["product_id"], name=products[g["product_id"]]["name"],
                                             name_plural=products[g["product_id"]]["name_plural"]),
                          status=STATUS[g["status"]], available=round(g["available"]),  # type: ignore[arg-type]
                          on_the_way=round(g["in_transit"] or 0),
                          days_of_cover=round(g["days_of_cover"], 1) if g["days_of_cover"] < 999 else None,
                          runs_low_day=weekday(g["runs_low_date"]), spare_units=round(g["spare_units"]))
            for g in rows
        ]
        return sorted(out, key=lambda i: (i.status != "RUNNING_LOW", i.store.name, i.product.name))

    # ---- ask -------------------------------------------------------------------------------------
    def ask(self, question: str) -> AskResponse:
        res = self.source.ask(question)
        answer = " ".join(res.answer.split())
        if res.answered:  # one plain sentence from the Ask space; our own fallback text is already short and kept whole
            answer = plain_sentence(answer, has_table=bool(res.rows))
            answer = "Here's what I found." if BANNED.search(answer) else answer
        table = None
        if res.columns and res.rows:
            table = AskTable(columns=[c.replace("_", " ").capitalize() for c in res.columns],
                             rows=[[_coerce(v) for v in row] for row in res.rows])
        return AskResponse(answered=res.answered, answer=answer, table=table)


def plain_sentence(text: str, has_table: bool, limit: int = 240) -> str:
    """Genie writes markdown and sometimes a list; planners get one clean sentence, with the detail in the table."""
    text = re.sub(r"[*`#_]{1,3}", "", text)
    text = " ".join(text.split())
    if has_table and re.search(r":\s+-\s", text):  # "Here are the totals: - a: 1 - b: 2" -> the lead-in only
        text = text.split(":", 1)[0] + "."
    sentence = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    if len(sentence) > limit:
        sentence = sentence[:limit].rsplit(" ", 1)[0].rstrip(",;: ") + "..."
    return sentence


def _coerce(v: Any) -> str | int | float | None:
    """Genie returns every cell as text; show numbers as numbers."""
    if isinstance(v, str) and re.fullmatch(r"-?\d+", v):
        return int(v)
    if isinstance(v, str) and re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    return v
