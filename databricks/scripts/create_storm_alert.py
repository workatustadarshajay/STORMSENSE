"""Creates a Databricks SQL alert that emails when urgent transfers are waiting for a decision.

Dry run by default: prints the alert definition and changes nothing. With --apply it creates the alert in the workspace.
Once it exists, Databricks emails the address whenever the check finds urgent moves, at most once an hour
(retrigger_seconds), and never on "all clear". The email comes from Databricks, so no mail password is needed.

    python3 scripts/create_storm_alert.py --email <address> --warehouse-id <id>            # dry run
    python3 scripts/create_storm_alert.py --email <address> --warehouse-id <id> --apply   # create it
"""

from __future__ import annotations

import argparse
import json
import re

NAME_OK = re.compile(r"[\w\-]+")


def definition(catalog: str, schema: str, warehouse_id: str, email: str) -> dict:
    from databricks.sdk.service import sql

    for part in (catalog, schema):
        if not NAME_OK.fullmatch(part):
            raise SystemExit(f"Unsafe catalog or schema name: {part!r}")
    query = (
        "SELECT COUNT(*) AS urgent_waiting "
        f"FROM `{catalog}`.`{schema}`.`transfer_recommendations` "
        "WHERE status = 'PENDING' AND urgency = 'URGENT'"
    )
    alert = sql.AlertV2(
        display_name="StormSense - Urgent moves waiting",
        query_text=query,
        warehouse_id=warehouse_id,
        evaluation=sql.AlertV2Evaluation(
            source=sql.AlertV2OperandColumn(name="urgent_waiting"),
            comparison_operator=sql.ComparisonOperator.GREATER_THAN,
            threshold=sql.AlertV2Operand(value=sql.AlertV2OperandValue(double_value=0.0)),
            notification=sql.AlertV2Notification(
                notify_on_ok=False,
                retrigger_seconds=3600,
                subscriptions=[sql.AlertV2Subscription(user_email=email)],
            ),
        ),
        schedule=sql.CronSchedule(
            quartz_cron_schedule="0 0 * * * ?",
            timezone_id="America/New_York",
            pause_status=sql.SchedulePauseStatus.UNPAUSED,
        ),
    )
    return alert


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--email", required=True, help="address that receives the alert")
    ap.add_argument("--warehouse-id", required=True)
    ap.add_argument("--catalog", default="workspace")
    ap.add_argument("--schema", default="stormsense")
    ap.add_argument("--profile", default="stormsense")
    ap.add_argument("--apply", action="store_true", help="create the alert in the workspace (sends emails when it triggers)")
    args = ap.parse_args()

    alert = definition(args.catalog, args.schema, args.warehouse_id, args.email)
    print(json.dumps(alert.as_dict(), indent=2))
    if not args.apply:
        print("\nDry run: nothing was created. Add --apply to create the alert.")
        return 0

    from databricks.sdk import WorkspaceClient

    created = WorkspaceClient(profile=args.profile).alerts_v2.create_alert(alert=alert)
    print(f"\nCreated alert {created.id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
