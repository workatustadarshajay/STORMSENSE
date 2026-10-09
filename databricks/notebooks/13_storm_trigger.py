# Databricks notebook source
# MAGIC %md
# MAGIC # 13 Storm trigger
# MAGIC
# MAGIC Every 15 minutes, reads the official National Weather Service warnings for Florida, Texas and California.
# MAGIC A new plan-changing warning (hurricane, tropical storm, storm, extreme wind, excessive heat, flash flood) starts the
# MAGIC daily cycle once, so the moves are redrawn on the new forecast. Planners still approve every move.
# MAGIC Each warning is recorded in `alerts_seen`, so it never triggers twice.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

from datetime import datetime, timezone

import pandas as pd
from databricks.sdk import WorkspaceClient

from stormsense_core import dbx
from stormsense_core.alerts import fetch_alerts, new_severe, parse_alerts

DAILY_JOB = "StormSense - Daily forecast and transfers"
ctx = dbx.Ctx(spark, dbutils)

# COMMAND ----------

seen = {r.alert_id for r in spark.sql(f"SELECT alert_id FROM {ctx.fq('alerts_seen')}").collect()}
alerts = parse_alerts(fetch_alerts())
fresh = new_severe(alerts, seen)
print(f"{len(alerts)} active warnings, {int(alerts.severe.sum())} plan-changing, {len(fresh)} new")
if fresh.empty:
    dbutils.notebook.exit("no new plan-changing warnings")

# COMMAND ----------

client = WorkspaceClient()
job = next(iter(client.jobs.list(name=DAILY_JOB)))
waiter = client.jobs.run_now(job_id=job.job_id)
now = datetime.now(timezone.utc).replace(tzinfo=None)
record = pd.DataFrame({
    "alert_id": fresh.alert_id, "event": fresh.event, "area": fresh.area,
    "onset": pd.to_datetime(fresh.onset, errors="coerce", utc=True).dt.tz_localize(None),
    "first_seen": now, "run_id": str(waiter.run_id),
})
ctx.frame(record, "alerts_seen").write.mode("append").saveAsTable(ctx.fq("alerts_seen"))
dbutils.notebook.exit(f"started the daily cycle for {len(fresh)} new warning(s)")
