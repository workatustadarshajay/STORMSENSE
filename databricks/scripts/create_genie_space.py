"""Creates (or updates) the Ask space: the tables it may read, what the words mean, and worked examples.

    python databricks/scripts/create_genie_space.py --profile stormsense --warehouse-id <id> [--catalog <name>] [--schema stormsense]

Prints the space id. Safe to re-run: an existing space with the same title is updated in place.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from databricks.sdk import WorkspaceClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stormsense_core.tables import GENIE_TABLES, TABLES  # noqa: E402

TITLE = "StormSense Ask"

INSTRUCTIONS = """\
You answer questions for retail planners about weather-driven demand and store-to-store transfers. Use plain words.
- A store is running low (SHORTAGE in inventory_gaps.status) when its stock is forecast to fall below the safety level this week. runs_low_date is the first day; stockout_date is the first day it sells out.
- A store has extra stock (SURPLUS) when it has well over two weeks of cover and can spare units without running low itself. spare_units is what it can give away.
- BALANCED means neither.
- Always use the latest as_of_date in inventory_gaps and predictions.
- A transfer is a recommended move of qty units of a product from source_store_id to dest_store_id. PENDING means waiting for a decision, APPROVED or REJECTED mean a planner decided. URGENT transfers are those where a store runs out within two days or a lot of sales are at risk.
- Show store and product names (stores.name, products.name), never ids. Weekday names are friendlier than dates for the coming week.
- weather_forecast uses the latest issued_at only. condition is storm, heavy_rain, heat, rain or clear.
- Only read data. Never change it.
"""

EXAMPLES = [
    ("Which stores will run out of generators this week?",
     "SELECT s.name AS store, g.runs_low_date, g.stockout_date, round(g.shortfall_units) AS units_short\n"
     "FROM {c}.inventory_gaps g JOIN {c}.stores s ON s.store_id = g.store_id JOIN {c}.products p ON p.product_id = g.product_id\n"
     "WHERE g.as_of_date = (SELECT max(as_of_date) FROM {c}.inventory_gaps) AND g.status = 'SHORTAGE' AND lower(p.name) LIKE '%generator%'\n"
     "ORDER BY g.runs_low_date"),
    ("Which stores have extra stock?",
     "SELECT s.name AS store, p.name AS product, round(g.spare_units) AS units_to_spare\n"
     "FROM {c}.inventory_gaps g JOIN {c}.stores s ON s.store_id = g.store_id JOIN {c}.products p ON p.product_id = g.product_id\n"
     "WHERE g.as_of_date = (SELECT max(as_of_date) FROM {c}.inventory_gaps) AND g.status = 'SURPLUS' ORDER BY g.spare_units DESC"),
    ("Which transfers are urgent?",
     "SELECT src.name AS from_store, dst.name AS to_store, p.name AS product, t.qty AS units, t.sales_protected_usd\n"
     "FROM {c}.transfer_recommendations t JOIN {c}.stores src ON src.store_id = t.source_store_id\n"
     "JOIN {c}.stores dst ON dst.store_id = t.dest_store_id JOIN {c}.products p ON p.product_id = t.product_id\n"
     "WHERE t.status = 'PENDING' AND t.urgency = 'URGENT' ORDER BY t.sales_protected_usd DESC"),
    ("How many units will Orlando sell this week by product?",
     "SELECT p.name AS product, round(sum(f.predicted_units)) AS units\n"
     "FROM {c}.predictions f JOIN {c}.stores s ON s.store_id = f.store_id JOIN {c}.products p ON p.product_id = f.product_id\n"
     "WHERE s.name = 'Orlando' AND f.as_of_date = (SELECT max(as_of_date) FROM {c}.predictions) GROUP BY p.name ORDER BY units DESC"),
    ("Where is bad weather coming this week?",
     "SELECT s.name AS store, w.forecast_date, w.condition, w.event_name\n"
     "FROM {c}.weather_forecast w JOIN {c}.stores s ON s.store_id = w.store_id\n"
     "WHERE w.issued_at = (SELECT max(issued_at) FROM {c}.weather_forecast) AND w.condition IN ('storm', 'heavy_rain', 'heat')\n"
     "ORDER BY w.forecast_date, s.name"),
]
QUESTIONS = [q for q, _ in EXAMPLES] + [
    "What is the total value of sales protected by pending transfers?",
    "Which products are running low in Texas?",
    "How much did we sell of coolers last week?",
]


def _id() -> str:
    return uuid.uuid4().hex


def serialized_space(catalog: str, schema: str) -> str:
    c = f"`{catalog}`.`{schema}`"
    tables = sorted(
        ({"identifier": f"{catalog}.{schema}.{t}", "description": [TABLES[t].comment]} for t in GENIE_TABLES),
        key=lambda t: t["identifier"],
    )
    return json.dumps({
        "version": 2,
        "config": {"sample_questions": sorted(({"id": _id(), "question": [q]} for q in QUESTIONS), key=lambda x: x["id"])},
        "data_sources": {"tables": tables},
        "instructions": {
            "text_instructions": [{"id": _id(), "content": [INSTRUCTIONS]}],
            "example_question_sqls": sorted(
                ({"id": _id(), "question": [q], "sql": [line + "\n" for line in sql.format(c=c).split("\n")]} for q, sql in EXAMPLES),
                key=lambda x: x["id"],
            ),
        },
    })


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--warehouse-id", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--schema", default="stormsense")
    a = ap.parse_args()

    w = WorkspaceClient(profile=a.profile)
    catalog = a.catalog or w.statement_execution.execute_statement(
        statement="SELECT current_catalog()", warehouse_id=a.warehouse_id, wait_timeout="30s").result.data_array[0][0]
    space = serialized_space(catalog, a.schema)

    existing = next((s for s in w.genie.list_spaces().spaces or [] if s.title == TITLE), None)
    if existing:
        w.genie.update_space(existing.space_id, serialized_space=space, warehouse_id=a.warehouse_id, title=TITLE)
        space_id = existing.space_id
    else:
        space_id = w.genie.create_space(a.warehouse_id, space, title=TITLE,
                                        description="Plain-English questions about stock, forecasts and transfers").space_id
    print(space_id)


if __name__ == "__main__":
    main()
