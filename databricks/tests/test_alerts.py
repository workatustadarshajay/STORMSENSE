"""The storm trigger reacts only to plan-changing warnings, and only once per warning."""
from stormsense_core.alerts import new_severe, parse_alerts

PAYLOAD = {"features": [
    {"id": "urn:nws:1", "properties": {"event": "Hurricane Warning", "areaDesc": "Coastal Lee", "onset": "2026-10-10T06:00:00-04:00"}},
    {"id": "urn:nws:2", "properties": {"event": "Wind Advisory", "areaDesc": "Harris", "onset": "2026-10-10T09:00:00-05:00"}},
    {"id": "urn:nws:3", "properties": {"event": "Excessive Heat Warning", "areaDesc": "Dallas", "onset": None,
                                       "effective": "2026-10-11T12:00:00-05:00"}},
]}


def test_parse_marks_only_plan_changing_warnings():
    alerts = parse_alerts(PAYLOAD)
    assert list(alerts.severe) == [True, False, True]
    assert alerts.iloc[2].onset == "2026-10-11T12:00:00-05:00"  # falls back to the effective time


def test_each_warning_triggers_once():
    alerts = parse_alerts(PAYLOAD)
    first = new_severe(alerts, seen=set())
    assert list(first.alert_id) == ["urn:nws:1", "urn:nws:3"]
    assert new_severe(alerts, seen={"urn:nws:1", "urn:nws:3"}).empty


def test_no_alerts_is_not_an_error():
    assert parse_alerts({}).empty
    assert new_severe(parse_alerts({"features": []}), set()).empty
