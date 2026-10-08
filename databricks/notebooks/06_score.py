# Databricks notebook source
# MAGIC %md
# MAGIC # 06 Score the next 7 days
# MAGIC
# MAGIC Loads the champion forecaster by alias and forecasts units per store, product and day for the 7 days after the stock date.
# MAGIC Re-running for the same day replaces that day's forecast only.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

import mlflow
import pandas as pd
from mlflow.tracking import MlflowClient

from stormsense_core import dbx
from stormsense_core.features import FEATURES

ctx = dbx.Ctx(spark, dbutils)
as_of = ctx.as_of()
mlflow.set_registry_uri("databricks-uc")
model_name = f"{ctx.catalog}.{ctx.schema}.demand_forecaster"

# COMMAND ----------

version = MlflowClient().get_model_version_by_alias(model_name, "champion").version
champion = mlflow.sklearn.load_model(f"models:/{model_name}@champion")

feats = ctx.read("features")
fut = feats[feats["is_future"]].copy()
fut["predicted_units"] = champion.predict(fut[FEATURES]).clip(min=0).round(2)
out = fut.rename(columns={"date": "forecast_date"})[["store_id", "product_id", "forecast_date", "predicted_units"]]
out = out.assign(as_of_date=as_of, model_name=model_name, model_version=str(version), run_ts=pd.Timestamp.utcnow().tz_localize(None))
n = ctx.write(out, "predictions", replace_where=f"as_of_date = '{as_of}'")
print(f"predictions: {n} rows for {as_of} from {model_name} version {version}")
