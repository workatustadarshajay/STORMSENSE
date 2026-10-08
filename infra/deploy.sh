#!/usr/bin/env bash
# Creates everything in the Databricks workspace from code, in the right order. Safe to re-run.
#   PROFILE=stormsense infra/deploy.sh          (asks before it starts)
#   YES=1 WAREHOUSE_ID=... infra/deploy.sh      (no prompt, explicit warehouse)
set -euo pipefail
cd "$(dirname "$0")/.."

PROFILE="${PROFILE:-stormsense}"
PY="${PY:-.venv/bin/python}"
db() { databricks "$@" --profile "$PROFILE"; }

echo "Workspace: $(db auth env 2>/dev/null | $PY -c 'import json,sys; print(json.load(sys.stdin)["env"]["DATABRICKS_HOST"])')"
if [ "${YES:-}" != "1" ]; then
  read -r -p "This creates tables, a forecaster, a daily job, an Ask space and an app, and runs serverless compute. Continue? [y/N] " ok
  [ "$ok" = "y" ] || { echo "Stopped."; exit 1; }
fi

# 1. A SQL warehouse: the one you name, otherwise the first serverless one.
WAREHOUSE_ID="${WAREHOUSE_ID:-$(db warehouses list -o json | $PY -c '
import json, sys
ws = json.load(sys.stdin)
pick = next((w for w in ws if w.get("enable_serverless_compute")), ws[0] if ws else None)
print(pick["id"] if pick else "")')}"
[ -n "$WAREHOUSE_ID" ] || { echo "No SQL warehouse found. Create a serverless one and set WAREHOUSE_ID."; exit 1; }
echo "Warehouse: $WAREHOUSE_ID"

# 2. Data side: notebooks and jobs, then build the tables and the forecaster.
(cd databricks && db bundle deploy && db bundle run stormsense_build)

# 3. The Ask space, over the tables that now exist.
SPACE_ID="$($PY databricks/scripts/create_genie_space.py --profile "$PROFILE" --warehouse-id "$WAREHOUSE_ID")"
echo "Ask space: $SPACE_ID"

# 4. The app.
make build-app
(cd backend && db bundle deploy --var "warehouse_id=$WAREHOUSE_ID" --var "genie_space_id=$SPACE_ID" && db bundle run stormsense)

# 5. Least-privilege access for the app's own service principal.
APP_SP="$(db apps get stormsense -o json | $PY -c 'import json,sys; print(json.load(sys.stdin)["service_principal_client_id"])')"
(cd databricks && db bundle run stormsense_app_access --params "app_service_principal=$APP_SP")

# 6. Check the real thing.
(cd backend && ../$PY scripts/smoke.py --profile "$PROFILE" --warehouse-id "$WAREHOUSE_ID" --space-id "$SPACE_ID")
echo "App: $(db apps get stormsense -o json | $PY -c 'import json,sys; print(json.load(sys.stdin)["url"])')"
