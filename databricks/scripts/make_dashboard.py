"""Writes the AI/BI (Lakeview) dashboard definition that the bundle deploys.

    python databricks/scripts/make_dashboard.py      # writes databricks/dashboards/stormsense_overview.lvdash.json

Every dataset queries the StormSense tables and views by their full three-part name, so the dashboard
works wherever the bundle is deployed.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "dashboards" / "stormsense_overview.lvdash.json"
T = "workspace.stormsense"
LATEST = f"(SELECT max(as_of_date) FROM {T}.inventory_gaps)"

DATASETS = {
    "kpi": f"""SELECT
  (SELECT count(*) FROM {T}.transfer_recommendations WHERE status = 'PENDING' AND urgency = 'URGENT') AS urgent,
  (SELECT count(*) FROM {T}.transfer_recommendations WHERE status = 'PENDING') AS pending,
  (SELECT round(sum(sales_protected_usd)) FROM {T}.transfer_recommendations WHERE status = 'PENDING') AS protected_usd,
  (SELECT count(DISTINCT store_id) FROM {T}.inventory_gaps WHERE status = 'SHORTAGE' AND as_of_date = {LATEST}) AS stores_at_risk""",
    "units_by_product": f"""SELECT p.name AS product, round(sum(f.predicted_units)) AS units
FROM {T}.predictions f JOIN {T}.products p ON p.product_id = f.product_id
WHERE f.as_of_date = (SELECT max(as_of_date) FROM {T}.predictions)
GROUP BY p.name ORDER BY units DESC""",
    "short_by_store": f"""SELECT s.name AS store, round(sum(g.shortfall_units)) AS units_short
FROM {T}.inventory_gaps g JOIN {T}.stores s ON s.store_id = g.store_id
WHERE g.status = 'SHORTAGE' AND g.as_of_date = {LATEST}
GROUP BY s.name ORDER BY units_short DESC""",
    "pending_transfers": f"""SELECT s1.name AS from_store, s2.name AS to_store, p.name AS product, t.qty AS units,
  t.urgency, round(t.sales_protected_usd) AS sales_protected_usd
FROM {T}.transfer_recommendations t
JOIN {T}.stores s1 ON s1.store_id = t.source_store_id
JOIN {T}.stores s2 ON s2.store_id = t.dest_store_id
JOIN {T}.products p ON p.product_id = t.product_id
WHERE t.status = 'PENDING'
ORDER BY (t.urgency = 'URGENT') DESC, t.sales_protected_usd DESC""",
    "accuracy": f"""SELECT model_version AS version, round(wape_model, 3) AS forecaster,
  round(wape_same_as_last_week, 3) AS same_as_last_week, round(wape_trailing_28d_avg, 3) AS trailing_28_day_average,
  CASE WHEN promoted THEN 'Champion' ELSE 'Not promoted' END AS status
FROM {T}.model_runs ORDER BY trained_at DESC""",
    "cost": f"""SELECT usage_date, round(sum(dbus), 2) AS dbus
FROM {T}.cost_daily GROUP BY usage_date ORDER BY usage_date""",
}


def counter(name: str, title: str, field: str, x: int) -> dict:
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": "kpi", "disaggregated": True,
                                                         "fields": [{"name": field, "expression": f"`{field}`"}]}}],
            "spec": {"version": 2, "widgetType": "counter",
                     "encodings": {"value": {"fieldName": field, "displayName": title}},
                     "frame": {"showTitle": True, "title": title}},
        },
        "position": {"x": x, "y": 0, "width": 2, "height": 3},
    }


def bar(name: str, dataset: str, title: str, cat: str, val: str, x: int, y: int, width: int, height: int) -> dict:
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "disaggregated": False, "fields": [
                {"name": cat, "expression": f"`{cat}`"},
                {"name": f"sum({val})", "expression": f"SUM(`{val}`)"}]}}],
            "spec": {"version": 3, "widgetType": "bar",
                     "encodings": {
                         "x": {"fieldName": cat, "scale": {"type": "categorical"}, "displayName": cat.replace("_", " ").capitalize()},
                         "y": {"fieldName": f"sum({val})", "scale": {"type": "quantitative"},
                               "displayName": val.replace("_", " ").capitalize()}},
                     "frame": {"showTitle": True, "title": title}},
        },
        "position": {"x": x, "y": y, "width": width, "height": height},
    }


def table(name: str, dataset: str, title: str, columns: list[str], x: int, y: int, width: int, height: int) -> dict:
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "disaggregated": True,
                                                         "fields": [{"name": c, "expression": f"`{c}`"} for c in columns]}}],
            "spec": {"version": 1, "widgetType": "table",
                     "encodings": {"columns": [{"fieldName": c, "title": c.replace("_", " ").capitalize(), "displayAs": "string",
                                                "type": "string", "order": i, "visible": True, "alignContent": "left"}
                                               for i, c in enumerate(columns)]},
                     "frame": {"showTitle": True, "title": title}},
        },
        "position": {"x": x, "y": y, "width": width, "height": height},
    }


def build() -> dict:
    layout = [
        counter("urgent", "Urgent transfers", "urgent", 0),
        counter("pending", "Transfers waiting", "pending", 2),
        counter("protected", "Sales protected (USD)", "protected_usd", 4),
        {"widget": {"name": "stores_at_risk", "queries": [{"name": "main_query", "query": {"datasetName": "kpi", "disaggregated": True,
                    "fields": [{"name": "stores_at_risk", "expression": "`stores_at_risk`"}]}}],
                    "spec": {"version": 2, "widgetType": "counter",
                             "encodings": {"value": {"fieldName": "stores_at_risk", "displayName": "Stores running low"}},
                             "frame": {"showTitle": True, "title": "Stores running low"}}},
         "position": {"x": 0, "y": 3, "width": 2, "height": 3}},
        bar("short_by_store", "short_by_store", "Units short this week, by store", "store", "units_short", 2, 3, 4, 6),
        bar("units_by_product", "units_by_product", "Units expected this week, by product", "product", "units", 0, 9, 3, 6),
        bar("cost", "cost", "Databricks usage for StormSense (DBUs per day)", "usage_date", "dbus", 3, 9, 3, 6),
        table("accuracy", "accuracy", "Forecast accuracy (lower is better)",
              ["version", "forecaster", "same_as_last_week", "trailing_28_day_average", "status"], 0, 15, 3, 4),
        table("transfers", "pending_transfers", "Transfers waiting for a decision",
              ["from_store", "to_store", "product", "units", "urgency", "sales_protected_usd"], 3, 15, 3, 6),
    ]
    return {
        "datasets": [{"name": n, "displayName": n.replace("_", " ").capitalize(), "query": q} for n, q in DATASETS.items()],
        "pages": [{"name": "overview", "displayName": "Overview", "pageType": "PAGE_TYPE_CANVAS", "layout": layout}],
    }


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(), indent=2) + "\n")
    print(f"wrote {OUT}")
