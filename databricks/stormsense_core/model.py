"""Train, validate and size the uncertainty of the demand forecaster (pure scikit-learn, no Spark)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from .features import CATEGORICAL, FEATURES

VALIDATION_DAYS = 28


def new_model() -> HistGradientBoostingRegressor:
    # Poisson loss suits unit counts; categorical store/product codes let one model serve every pair.
    return HistGradientBoostingRegressor(
        loss="poisson", learning_rate=0.06, max_iter=400, max_leaf_nodes=31, min_samples_leaf=20,
        l2_regularization=1.0, categorical_features=[FEATURES.index(c) for c in CATEGORICAL], random_state=42,
    )


def wape(actual: np.ndarray, pred: np.ndarray) -> float:
    return float(np.abs(actual - pred).sum() / max(actual.sum(), 1e-9))


def mape(actual: np.ndarray, pred: np.ndarray) -> float:
    m = actual > 0  # undefined at zero, so secondary only
    return float(np.mean(np.abs(actual[m] - pred[m]) / actual[m]))


@dataclass
class Trained:
    model: HistGradientBoostingRegressor
    metrics: dict[str, float]
    intervals: pd.DataFrame  # product_id, ratio_p10, ratio_p90, windows
    validation_start: pd.Timestamp


def fit(features: pd.DataFrame, validation_days: int = VALIDATION_DAYS) -> Trained:
    """Time-based split: train on everything before the last `validation_days`, validate on those days."""
    hist = features[~features["is_future"]].dropna(subset=["units"])
    cut = hist["date"].max() - pd.Timedelta(days=validation_days - 1)
    train, val = hist[hist["date"] < cut], hist[hist["date"] >= cut].copy()

    model = new_model().fit(train[FEATURES], train["units"])
    val["pred"] = model.predict(val[FEATURES])
    a, p = val["units"].to_numpy(float), val["pred"].to_numpy(float)
    metrics = {
        "wape_model": wape(a, p),
        "wape_same_as_last_week": wape(a, val["sales_lag7"].to_numpy(float)),
        "wape_trailing_28d_avg": wape(a, val["avg28_lag7"].to_numpy(float)),
        "mape_model": mape(a, p),
        "train_rows": float(len(train)), "validation_rows": float(len(val)),
    }

    # Weekly demand: actual / predicted over every rolling 7-day window of the validation period.
    win = (val.sort_values("date").set_index("date")
              .groupby(["store_id", "product_id"])[["units", "pred"]].rolling(7).sum().dropna().reset_index())
    win = win[win["pred"] > 0]
    win["ratio"] = win["units"] / win["pred"]
    iv = win.groupby("product_id")["ratio"].agg(
        ratio_p10=lambda r: float(np.quantile(r, 0.10)), ratio_p90=lambda r: float(np.quantile(r, 0.90)), windows="size"
    ).reset_index()
    return Trained(model, metrics, iv, cut)
