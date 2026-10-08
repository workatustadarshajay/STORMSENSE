# Databricks notebook source
# MAGIC %md
# MAGIC # 04 Train and register the forecaster
# MAGIC
# MAGIC Trains a gradient-boosted regressor on everything before the last four weeks and checks it on those four weeks (a time split, never random).
# MAGIC Compares it with two simple baselines. Only a forecaster that beats both is registered in Unity Catalog and given the alias `champion`.
# MAGIC Everything downstream loads it by that alias.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

import mlflow
import pandas as pd
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient

from stormsense_core import dbx, model
from stormsense_core.features import FEATURES

ctx = dbx.Ctx(spark, dbutils)
mlflow.set_registry_uri("databricks-uc")
model_name = f"{ctx.catalog}.{ctx.schema}.demand_forecaster"
mlflow.set_experiment("/Shared/stormsense-demand-forecast")

# COMMAND ----------

feats = ctx.read("features")
feats["date"] = pd.to_datetime(feats["date"])
trained = model.fit(feats)
m = trained.metrics
print({k: round(v, 3) for k, v in m.items()})
beats_both = m["wape_model"] < m["wape_same_as_last_week"] and m["wape_model"] < m["wape_trailing_28d_avg"]

# COMMAND ----------

val = feats[(~feats["is_future"]) & (feats["date"] >= trained.validation_start)]
with mlflow.start_run(run_name="demand-forecaster") as run:
    mlflow.log_params({"loss": "poisson", "validation_days": model.VALIDATION_DAYS, "features": ",".join(FEATURES)})
    mlflow.log_metrics(m)
    info = mlflow.sklearn.log_model(
        trained.model, "model",
        signature=infer_signature(val[FEATURES], trained.model.predict(val[FEATURES])),
        input_example=val[FEATURES].head(5), registered_model_name=model_name,
    )
version = str(info.registered_model_version)
client = MlflowClient()
if beats_both:
    client.set_registered_model_alias(model_name, "champion", version)
print(f"{model_name} version {version}: {'now champion' if beats_both else 'NOT promoted, it did not beat both baselines'}")

# COMMAND ----------

now = pd.Timestamp.utcnow().tz_localize(None)
ctx.write(pd.DataFrame([{"run_id": run.info.run_id, "trained_at": now, "model_version": version, **{k: m[k] for k in (
    "wape_model", "wape_same_as_last_week", "wape_trailing_28d_avg", "mape_model")},
    "validation_start": trained.validation_start, "promoted": beats_both}]).astype({"validation_start": "datetime64[ns]"}),
    "model_runs", replace_where=f"run_id = '{run.info.run_id}'")
iv = trained.intervals.assign(model_version=version, trained_at=now)
ctx.write(iv, "forecast_intervals", replace_where=f"model_version = '{version}'")
if not beats_both:
    raise RuntimeError("The new forecaster did not beat both baselines, so the current champion stays. See model_runs.")
