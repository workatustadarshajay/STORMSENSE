import sys
from datetime import date, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stormsense_core import features, model, planning, reference, synth  # noqa: E402

END = date(2026, 10, 7)


@pytest.fixture(scope="session")
def pipeline():
    """The whole daily cycle on sample data, run once for all tests."""
    tables = synth.generate(END).tables
    feats = features.build_features(tables["sales_history"], tables["weather_observed"], tables["weather_forecast"], END)
    trained = model.fit(feats)
    fut = feats[feats["is_future"]].copy()
    fut["predicted_units"] = trained.model.predict(fut[features.FEATURES]).clip(min=0)
    preds = fut.rename(columns={"date": "forecast_date"})[["store_id", "product_id", "forecast_date", "predicted_units"]]
    inv = tables["inventory_snapshot"]
    inv = inv[inv["snapshot_date"] == END]
    settings = {k: float(v) for k, v in reference.SETTINGS.items()}
    gaps = planning.compute_gaps(preds, inv, planning.committed_from_recs(None, END), trained.intervals, settings, END)
    recs = planning.recommend_transfers(gaps, reference.stores_df(), reference.products_df(),
                                        tables["weather_forecast"], settings, END, datetime(2026, 10, 8, 6))
    return dict(tables=tables, feats=feats, trained=trained, preds=preds, inv=inv, gaps=gaps, recs=recs, settings=settings)
