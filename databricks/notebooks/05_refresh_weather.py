# Databricks notebook source
# MAGIC %md
# MAGIC # 05 Refresh weather
# MAGIC
# MAGIC Brings in the latest ten-day forecast for every store. `sample` re-issues the sample forecast; `nws` calls the US National Weather Service
# MAGIC and fails loudly if it cannot, rather than quietly serving old weather. Re-running on the same day replaces that day's issue.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

from datetime import datetime, timedelta, timezone

import pandas as pd

from stormsense_core import dbx, reference, synth, weather
from stormsense_core.tables import TABLES

ctx = dbx.Ctx(spark, dbutils)
dbutils.widgets.dropdown("provider", "sample", ["sample", "nws"], "Weather provider")
provider = dbutils.widgets.get("provider")
as_of = ctx.as_of()
now = datetime.now(timezone.utc).replace(tzinfo=None)

# COMMAND ----------

if provider == "nws":
    fc = weather.fetch_nws_forecast(reference.stores_df())
    fc["forecast_date"] = pd.to_datetime(fc["forecast_date"])
    fc = fc[fc["forecast_date"] > pd.Timestamp(as_of)]
    needed = {pd.Timestamp(as_of) + timedelta(days=i) for i in range(1, 8)}
    if not needed <= set(fc["forecast_date"]):
        raise RuntimeError(f"The live forecast does not cover the 7 days after the stock date ({as_of}). Refresh stock data first, or use the sample provider.")
else:
    fc = synth.forecast_from_truth(synth.simulate_weather(as_of), as_of).drop(columns=["issued_at", "issued_date"])
fc["issued_at"], fc["issued_date"] = now, now.date()
cols = [name for name, _, _ in TABLES["weather_forecast"].columns]
n = ctx.write(fc[cols], "weather_forecast", replace_where=f"issued_date = '{now.date()}'")
print(f"{provider}: wrote {n} forecast rows for {fc['store_id'].nunique()} stores, issued {now:%Y-%m-%d %H:%M} UTC")
