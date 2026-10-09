# Databricks notebook source
# MAGIC %md
# MAGIC # 08 Transfer recommendations
# MAGIC
# MAGIC Matches stores with extra stock to stores running short, nearest first, per product. A source never gives away more than it can spare.
# MAGIC Merges into the table: only PENDING rows are refreshed or removed. Approved and rejected rows are never changed, and the same
# MAGIC source, destination and product is never pending twice.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

from datetime import datetime, timezone

import pandas as pd

from stormsense_core import dbx, planning

ctx = dbx.Ctx(spark, dbutils)
as_of = ctx.as_of()

# COMMAND ----------

gaps = ctx.read("inventory_gaps")
gaps = gaps[pd.to_datetime(gaps["as_of_date"]).dt.date == as_of]
wx = ctx.read("weather_forecast")
wx = wx[wx["issued_at"] == wx["issued_at"].max()]
prefs = ctx.read("route_preferences")  # learned from planner rejections; ranks routes, never adds or removes moves
recs = planning.recommend_transfers(gaps, ctx.read("stores"), ctx.read("products"), wx, ctx.setting_values(), as_of,
                                    datetime.now(timezone.utc).replace(tzinfo=None), route_preferences=prefs)
print(f"{len(recs)} recommendations,", recs["urgency"].value_counts().to_dict() if len(recs) else {})

# COMMAND ----------

ctx.frame(recs, "transfer_recommendations").createOrReplaceTempView("new_recs")
spark.sql(f"""
    MERGE INTO {ctx.fq("transfer_recommendations")} t USING new_recs s
    ON t.status = 'PENDING' AND t.as_of_date = s.as_of_date AND t.source_store_id = s.source_store_id
       AND t.dest_store_id = s.dest_store_id AND t.product_id = s.product_id
    WHEN MATCHED THEN UPDATE SET qty = s.qty, urgency = s.urgency, confidence = s.confidence, confidence_level = s.confidence_level,
         reason = s.reason, sales_protected_usd = s.sales_protected_usd, distance_miles = s.distance_miles,
         runs_low_date = s.runs_low_date, created_at = s.created_at
    WHEN NOT MATCHED THEN INSERT *
    WHEN NOT MATCHED BY SOURCE AND t.status = 'PENDING' THEN DELETE
""")
display(spark.sql(f"SELECT status, urgency, count(*) AS transfers FROM {ctx.fq('transfer_recommendations')} GROUP BY ALL ORDER BY status, urgency"))
