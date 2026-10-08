"""Weather classification and the live forecast adapter."""
from __future__ import annotations

import json
import re
import urllib.request
from datetime import date, datetime, timezone

import pandas as pd

# Display label and demand driver for each condition we alert on.
CONDITION_LABELS = {"storm": "Storm", "heavy_rain": "Heavy rain", "heat": "Heat wave"}
SEVERITY = ["storm", "heavy_rain", "heat"]  # worst first


def classify(wind_max_mph: float, rain_in: float, temp_max_f: float) -> str:
    if wind_max_mph >= 45 or (rain_in >= 2.0 and wind_max_mph >= 35):
        return "storm"
    if rain_in >= 1.5:
        return "heavy_rain"
    if temp_max_f >= 97:
        return "heat"
    if rain_in >= 0.25:
        return "rain"
    return "clear"


def worst_event(weather: pd.DataFrame, conditions: list[str] = SEVERITY) -> tuple[str, date, str | None] | None:
    """Worst of `conditions` (listed worst first) in a store's forecast: (condition, first day, event name)."""
    for cond in conditions:
        hit = weather[weather["condition"] == cond].sort_values("forecast_date")
        if len(hit):
            row = hit.iloc[0]
            name = row.get("event_name")
            return cond, pd.Timestamp(row["forecast_date"]).date(), (name if isinstance(name, str) else None)
    return None


def weather_phrase(event: tuple[str, date, str | None] | None) -> str:
    if event is None:
        return "Demand is rising"
    cond, day, name = event
    return f"{name or CONDITION_LABELS[cond]} expected {day.strftime('%A')}"


# ---- Live provider: National Weather Service (US only, no key) -------------------------------

_NWS = "https://api.weather.gov"


def _get(url: str, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "stormsense-weather/1.0", "Accept": "application/geo+json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https host)
        return json.load(resp)


def _celsius_to_f(c: float) -> float:
    return c * 9 / 5 + 32


_DURATION = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?)?")


def parse_nws_grid(grid: dict, days: int = 10) -> pd.DataFrame:
    """Daily temp/wind/rain from an NWS gridpoint payload (pure function, unit-tested)."""
    props = grid["properties"]

    def hourly(name: str, spread: bool = False) -> pd.Series:
        pts: dict[pd.Timestamp, float] = {}
        for item in props.get(name, {}).get("values", []):
            if item["value"] is None:
                continue
            start, _, dur = item["validTime"].partition("/")
            m = _DURATION.fullmatch(dur)
            hours = max(1, int(m.group(1) or 0) * 24 + int(m.group(2) or 0)) if m else 1
            t0 = pd.Timestamp(start)
            for h in range(min(hours, 48)):
                pts[t0 + pd.Timedelta(hours=h)] = item["value"] / hours if spread else item["value"]
        return pd.Series(pts, dtype="float64").sort_index()

    temp = hourly("temperature").map(_celsius_to_f)
    gust = hourly("windGust").combine_first(hourly("windSpeed")) * 0.621371  # km/h -> mph
    rain = hourly("quantitativePrecipitation", spread=True) / 25.4  # mm per period -> in per hour
    out = pd.DataFrame({"temp": temp, "gust": gust, "rain": rain})
    out["day"] = out.index.tz_convert("UTC").date  # ponytail: UTC days; switch to store time zone for production
    daily = out.groupby("day").agg(temp_max_f=("temp", "max"), temp_min_f=("temp", "min"),
                                   wind_max_mph=("gust", "max"), rain_in=("rain", "sum"))
    daily = daily.dropna(subset=["temp_max_f"]).fillna({"wind_max_mph": 0.0, "rain_in": 0.0}).head(days)
    daily.index.name = "forecast_date"
    return daily.round(1).reset_index()


def fetch_nws_forecast(stores: pd.DataFrame, days: int = 10) -> pd.DataFrame:
    """Live forecast for every store. Raises on any provider error so callers can fall back."""
    issued = datetime.now(timezone.utc)
    frames = []
    for s in stores.itertuples():
        point = _get(f"{_NWS}/points/{s.latitude:.4f},{s.longitude:.4f}")
        grid = _get(point["properties"]["forecastGridData"])
        daily = parse_nws_grid(grid, days)
        daily.insert(0, "store_id", s.store_id)
        frames.append(daily)
    df = pd.concat(frames, ignore_index=True)
    df["condition"] = [classify(w, r, t) for w, r, t in zip(df.wind_max_mph, df.rain_in, df.temp_max_f)]
    df["event_name"] = None
    df["issued_at"] = issued
    df["issued_date"] = issued.date()
    return df
