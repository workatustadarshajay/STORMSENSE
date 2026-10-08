# Runbook

All commands run from the repository root. `PROFILE` defaults to `stormsense`.

## First deployment

```bash
databricks auth login --host https://<your-workspace>.cloud.databricks.com --profile stormsense
make deploy            # shows the workspace and asks before it starts
```

`make deploy` runs `infra/deploy.sh`, which, in order: picks a serverless SQL warehouse, deploys the data bundle and runs the build job (tables, sample data, features, forecaster, forecasts, gaps, recommendations, verification), creates the Ask space, builds and deploys the app, grants the app's service principal least-privilege access, and runs the smoke test against the live workspace. It is safe to re-run.

## Everyday tasks

| Task | How |
|---|---|
| Add a planner or viewer | `INSERT INTO <catalog>.stormsense.app_users VALUES ('name@company.com', 'Name', 'planner')`. Also grant them access to the app (App permissions, Can use). |
| Change a threshold | `UPDATE <catalog>.stormsense.settings SET value = '14' WHERE key = 'surplus_threshold_days'`; effective on the next run. |
| Run the daily cycle now | `cd databricks && databricks bundle run stormsense_daily --profile stormsense` |
| Pause or resume the 6:00 AM schedule | `make pause` / `make resume` |
| Rebuild everything on fresh sample data | `cd databricks && databricks bundle run stormsense_build --profile stormsense` |
| Use the live US weather forecast | Deploy with `--var weather_provider=nws`. It needs stock data dated yesterday (rebuild first), and fails loudly if the provider is down. |
| Use a catalog other than the workspace default | Pass `--var catalog=<name>` to the data bundle, and set `STORMSENSE_CATALOG` in `backend/app.yaml` and `backend/databricks.yml`. |
| Run the app on your machine against the workspace | Copy `infra/.env.example` to `backend/.env`, set `STORMSENSE_MODE=databricks`, the warehouse and space ids, and `STORMSENSE_DATABRICKS_PROFILE`. |

## When the daily job fails

1. You get an email from the failed run. Open it and find the red task.
2. Re-run just that task from the run page ("Repair run"). Every task is idempotent.
3. Common causes:
   * **Weather refresh** (provider `nws`): the provider is down or the stock date is stale. Switch to `sample` or refresh stock data, then repair the run.
   * **Forecast**: no `champion` alias. Run the build job; the forecaster is only promoted if it beats both baselines.
   * **Verify**: the message lists exactly which check failed (for example, forecasts missing for a store). Fix the cause and repair the run.
4. The app keeps serving the last good forecast and recommendations while a run is failing.

## When the app says "Getting things ready"

The SQL warehouse is starting (serverless usually takes a few seconds) or busy. Pages retry on their own for about a minute. If it persists:

* `databricks warehouses get <id> --profile stormsense` shows the state. Start it with `databricks warehouses start <id>`.
* `databricks apps logs stormsense --profile stormsense` shows the app's own logs (requires OAuth login, not a token).

If a page says "That didn't load" instead, the query itself failed; the cause is in the app logs with the statement id.

## When `bundle deploy` says "access denied" behind a company proxy

If `databricks bundle deploy` fails with `access denied` or "possible permission error", but you are the owner of the bundle folder, look at the response (`--debug`). If it is an HTML page from a web filter (for example "blocked in accordance with the ... Internet Usage Policy") rather than a Databricks error, the proxy is rejecting that upload, not Databricks.

* Confirm which file: upload each file on its own with `curl -X POST "$HOST/api/2.0/workspace-files/import-file/<path>?overwrite=true" -H "Authorization: Bearer $(databricks auth token ...)" --data-binary @file`. A blocked file returns 403 every time.
* Ask the network team to allow uploads to your workspace host, or deploy from a place the proxy does not inspect (a CI runner using a service principal, for example).
* Do not reshape files to get past a filter: that is the control working as designed, and it needs an owner's decision.
* The app's static build deliberately contains only `.html`, `.js` and `.css`: the workspace also refuses binary font files, so fonts are embedded in the stylesheet at build time.

## Cost and housekeeping

* Check the **Usage** page in your account daily while on trial credits.
* The warehouse should auto-stop after the shortest option.
* Pause the schedule when you are not demoing (`make pause`).
* Keep this repository in Git: it is the source of truth if the workspace goes away. `make dev` runs the complete app on sample data with no workspace at all.
