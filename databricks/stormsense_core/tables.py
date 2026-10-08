"""Table definitions: one place for DDL, column comments (which also teach Genie) and the data dictionary."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Table:
    comment: str
    columns: list[tuple[str, str, str]]  # name, SQL type, comment


_WX = [
    ("temp_max_f", "DOUBLE", "Highest temperature of the day, degrees Fahrenheit"),
    ("temp_min_f", "DOUBLE", "Lowest temperature of the day, degrees Fahrenheit"),
    ("rain_in", "DOUBLE", "Rainfall for the day, inches"),
    ("wind_max_mph", "DOUBLE", "Strongest wind gust of the day, miles per hour"),
    ("condition", "STRING", "storm, heavy_rain, heat, rain or clear"),
    ("event_name", "STRING", "Name of the storm or heat event, when there is one"),
]

TABLES: dict[str, Table] = {
    "stores": Table("Retail stores with location and region", [
        ("store_id", "STRING", "Store code, for example S01"),
        ("name", "STRING", "Friendly store name"),
        ("city", "STRING", "City"),
        ("region", "STRING", "Florida, Texas or California"),
        ("latitude", "DOUBLE", "Latitude"),
        ("longitude", "DOUBLE", "Longitude"),
        ("time_zone", "STRING", "IANA time zone"),
        ("size_factor", "DOUBLE", "Relative store size, 1.0 is typical"),
    ]),
    "products": Table("Products the planners move between stores", [
        ("product_id", "STRING", "Product code, for example P01"),
        ("name", "STRING", "Friendly product name, singular"),
        ("name_plural", "STRING", "Friendly product name, plural, used in sentences"),
        ("category", "STRING", "Product category"),
        ("unit_cost", "DOUBLE", "Cost per unit, US dollars"),
        ("unit_price", "DOUBLE", "Selling price per unit, US dollars"),
        ("pack_size", "INT", "Units per pack; transfers move whole packs"),
        ("weather_driver", "STRING", "What lifts demand: wind (storms), rain or heat"),
    ]),
    "settings": Table("Planning thresholds, editable without code changes", [
        ("key", "STRING", "Setting name"),
        ("value", "STRING", "Setting value"),
    ]),
    "weather_observed": Table("Observed daily weather per store", [
        ("store_id", "STRING", "Store code"), ("obs_date", "DATE", "Day observed"), *_WX,
    ]),
    "weather_forecast": Table("Daily weather forecast per store; the latest issued_at is current", [
        ("store_id", "STRING", "Store code"), ("forecast_date", "DATE", "Day being forecast"), *_WX,
        ("issued_at", "TIMESTAMP", "When the forecast was issued"),
        ("issued_date", "DATE", "Date part of issued_at"),
    ]),
    "sales_history": Table("Units sold per store, product and day", [
        ("store_id", "STRING", "Store code"), ("product_id", "STRING", "Product code"),
        ("sale_date", "DATE", "Day of sale"), ("units", "BIGINT", "Units sold"),
        ("revenue_usd", "DOUBLE", "Sales value, US dollars"),
    ]),
    "inventory_snapshot": Table("End-of-day stock per store and product", [
        ("store_id", "STRING", "Store code"), ("product_id", "STRING", "Product code"),
        ("snapshot_date", "DATE", "Day of the snapshot"), ("on_hand", "BIGINT", "Units on the shelf and in the back room"),
        ("in_transit", "BIGINT", "Units already on the way to the store"),
    ]),
    "predictions": Table("Forecast units per store, product and day for the next 7 days", [
        ("as_of_date", "DATE", "Last day of data the forecast used"),
        ("store_id", "STRING", "Store code"), ("product_id", "STRING", "Product code"),
        ("forecast_date", "DATE", "Day being forecast"),
        ("predicted_units", "DOUBLE", "Forecast units sold that day"),
        ("model_name", "STRING", "Registered forecaster name"), ("model_version", "STRING", "Registered forecaster version"),
        ("run_ts", "TIMESTAMP", "When the forecast was made"),
    ]),
    "forecast_intervals": Table("Typical forecast error per product, measured on the most recent four weeks", [
        ("product_id", "STRING", "Product code"),
        ("ratio_p10", "DOUBLE", "Low case: actual weekly demand / forecast, 10th percentile"),
        ("ratio_p90", "DOUBLE", "High case: actual weekly demand / forecast, 90th percentile"),
        ("windows", "BIGINT", "Weekly windows measured"),
        ("model_version", "STRING", "Forecaster version measured"), ("trained_at", "TIMESTAMP", "When it was measured"),
    ]),
    "model_runs": Table("Forecast accuracy for each training run", [
        ("run_id", "STRING", "Training run id"), ("trained_at", "TIMESTAMP", "When it trained"),
        ("model_version", "STRING", "Registered forecaster version"),
        ("wape_model", "DOUBLE", "Weighted absolute error of the forecaster on the last four weeks (lower is better)"),
        ("wape_same_as_last_week", "DOUBLE", "Same measure for 'same as last week'"),
        ("wape_trailing_28d_avg", "DOUBLE", "Same measure for 'average of the last 28 days'"),
        ("mape_model", "DOUBLE", "Mean absolute percentage error, secondary"),
        ("validation_start", "DATE", "First day of the four-week check"),
        ("promoted", "BOOLEAN", "True when it beat both baselines and became the champion"),
    ]),
    "inventory_gaps": Table("Projected stock for the next 7 days; status is SHORTAGE, SURPLUS or BALANCED", [
        ("as_of_date", "DATE", "Last day of data used"), ("store_id", "STRING", "Store code"),
        ("product_id", "STRING", "Product code"),
        ("on_hand", "BIGINT", "Units on hand"), ("in_transit", "BIGINT", "Units on the way"),
        ("committed_in", "DOUBLE", "Units arriving from approved transfers"),
        ("committed_out", "DOUBLE", "Units leaving for approved transfers"),
        ("available", "DOUBLE", "on_hand + in_transit + committed_in - committed_out"),
        ("forecast_units", "DOUBLE", "Forecast units sold over the next 7 days"),
        ("forecast_p10", "DOUBLE", "Low case for the 7 days"), ("forecast_p90", "DOUBLE", "High case for the 7 days"),
        ("avg_daily", "DOUBLE", "Average units sold per day over the horizon"),
        ("safety_stock", "DOUBLE", "Units to keep in reserve"),
        ("days_of_cover", "DOUBLE", "How many days the available stock lasts at the forecast pace"),
        ("runs_low_date", "DATE", "First day stock falls below the safety level"),
        ("stockout_date", "DATE", "First day stock runs out"),
        ("shortfall_units", "DOUBLE", "Units missing to stay above the safety level for 7 days"),
        ("shortfall_p10", "DOUBLE", "Shortfall in the low demand case"), ("shortfall_p90", "DOUBLE", "Shortfall in the high demand case"),
        ("lost_units", "DOUBLE", "Units of demand that would go unmet"),
        ("spare_units", "DOUBLE", "Units that can be given away without creating a shortage"),
        ("status", "STRING", "SHORTAGE, SURPLUS or BALANCED"),
    ]),
    "transfer_recommendations": Table("Recommended store-to-store moves and the planner's decision", [
        ("rec_id", "STRING", "Recommendation id"), ("as_of_date", "DATE", "Data day it was made for"),
        ("source_store_id", "STRING", "Store giving stock"), ("dest_store_id", "STRING", "Store receiving stock"),
        ("product_id", "STRING", "Product code"), ("qty", "BIGINT", "Units to move"),
        ("urgency", "STRING", "URGENT or NORMAL"), ("confidence", "DOUBLE", "Share of the move still needed in the low demand case"),
        ("confidence_level", "STRING", "High, Medium or Low"), ("reason", "STRING", "Plain-English reason"),
        ("sales_protected_usd", "DOUBLE", "Sales value protected by the move, US dollars"),
        ("distance_miles", "BIGINT", "Distance between the stores"),
        ("runs_low_date", "DATE", "Day the destination starts running low"),
        ("status", "STRING", "PENDING, APPROVED or REJECTED"), ("created_at", "TIMESTAMP", "When it was recommended"),
        ("decided_by", "STRING", "Who approved or rejected it"), ("decided_at", "TIMESTAMP", "When it was decided"),
        ("decision_note", "STRING", "Note or rejection reason"),
        ("decision_request_id", "STRING", "Request that made the decision"),
    ]),
    "transfer_audit": Table("Every approval and rejection, with who, when and from which request", [
        ("audit_id", "STRING", "Audit row id"), ("event_ts", "TIMESTAMP", "When it happened"),
        ("actor", "STRING", "Who did it"), ("action", "STRING", "APPROVED, REJECTED or SKIPPED"),
        ("rec_id", "STRING", "Recommendation id"), ("request_id", "STRING", "Request id"), ("note", "STRING", "Note"),
    ]),
    "app_users": Table("Who can use the planning app, and what they may do", [
        ("email", "STRING", "Sign-in email"), ("display_name", "STRING", "Name shown in the app"),
        ("role", "STRING", "viewer, planner or admin"),
    ]),
}

# What Genie may read. Decision logs, accounts and internals stay out.
GENIE_TABLES = ["stores", "products", "predictions", "inventory_gaps", "transfer_recommendations",
                "sales_history", "inventory_snapshot", "weather_forecast"]


def _quote(text: str) -> str:
    """A SQL string literal. Spark reads a doubled quote as two joined strings, so escape with a backslash."""
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"


def create_sql(fq_name: str, t: Table) -> str:
    cols = ",\n  ".join(f"`{n}` {typ} COMMENT {_quote(c)}" for n, typ, c in t.columns)
    return f"CREATE TABLE IF NOT EXISTS {fq_name} (\n  {cols}\n) COMMENT {_quote(t.comment)}"


def data_dictionary() -> str:
    out = ["# Data dictionary", "", "Generated from `databricks/stormsense_core/tables.py` by `make docs`. Do not edit by hand.", ""]
    for name, t in TABLES.items():
        out += [f"## `{name}`", "", t.comment + ".", "", "| Column | Type | Meaning |", "|---|---|---|"]
        out += [f"| `{n}` | {typ} | {c} |" for n, typ, c in t.columns]
        out.append("")
    return "\n".join(out)
