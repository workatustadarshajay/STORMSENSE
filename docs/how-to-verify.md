# How to verify

Each milestone has a quick local check (no workspace) and, where it applies, a check on the real workspace.

## 1. Databricks foundation and data

**Local:** `make test` runs `databricks/tests`. They prove: the sample data is reproducible; the history holds at least four named storm or heat events and a year of days; **generators sell 3x or more on storm days and coolers 1.3x or more on hot days**; the upcoming week contains a storm and a heat wave; the latest stock has both shortage and surplus.

**Workspace:** the build job ends with `09_verify` in `build` mode, which fails loudly. Run `cd databricks && databricks bundle run stormsense_build --profile stormsense`; every task, including `verify`, must be green. In the run output, `verify` prints one PASS line per check.

## 2. Features and the forecaster

**Local:** the same tests prove the split is by time (last 28 days held out), the lag-7 features equal the sales exactly 7 days earlier, the target is in no feature, intervals come from validation windows, and **the forecaster beats both baselines on WAPE**.

**Workspace:** open the Experiments page, experiment `/Shared/stormsense-demand-forecast`, and the latest run's metrics (`wape_model` below both baseline metrics). In Catalog, `<catalog>.stormsense.demand_forecaster` has alias `champion`. `SELECT * FROM <catalog>.stormsense.model_runs` shows the same numbers and `promoted = true`.

## 3. Forecasts, gaps and transfers

**Local:** tests prove at least five pending recommendations; minimum quantity, distance limit and pack multiples are respected; a source never gives more than it can spare; no store both gives and receives a product; approved transfers count as arriving stock and are not recommended again.

**Workspace:** `SELECT status, count(*) FROM <catalog>.stormsense.inventory_gaps GROUP BY status` shows SHORTAGE and SURPLUS. `SELECT status, urgency, count(*) FROM ...transfer_recommendations GROUP BY ALL` shows at least five PENDING. Re-run `08_recommendations`: the counts do not change and nothing non-pending is touched.

## 4. Daily job

**Workspace:** `databricks bundle run stormsense_daily` succeeds end to end (six tasks) and `predictions` has 350 rows for the latest `as_of_date`. In the job's settings the schedule reads 6:00 AM America/New_York, retries are 2 per task, and failure email goes to the deploying account. Run it twice: results are identical (idempotent).

## 5. API

**Local:** `python -m pytest backend`. Includes a contract test for every endpoint, a test that the words on the banned list never reach any response, `test_sql.py` (parameter binding, plus a static check that no request data is interpolated into SQL), `test_approvals.py` (approve, repeat, mixed, audit rows, viewers refused, cross-site posts refused) and `test_security.py` (headers, size limit, rate limit, waking-up and failure states).

**Workspace:** `make smoke WAREHOUSE_ID=<id> SPACE_ID=<id>` exercises the real warehouse and Ask space through the app's own code, answers ten sample questions, and proves Ask cannot change data.

## 6. Web app

**Local:** `cd frontend && npm test` (component tests: approve flow, the "already handled by someone else" message, a double-click sending one request, rejecting needing a reason, viewers, every loading, empty, error and waking-up state, and a scan for technical words on every screen). `make e2e` drives the built app in a real browser on a desktop and a phone viewport, runs an accessibility scan (WCAG 2 A and AA, serious and critical findings must be zero), checks for browser errors including content-security-policy violations, and has two browsers approve the same transfer.

## 7. Packaging

`make lint` is clean; `docker compose -f infra/docker-compose.yml up --build` serves the app on http://localhost:8000 on sample data; CI (`.github/workflows/ci.yml`) runs lint, every test, the contract check (generated types, sample data and data dictionary are current) and the browser tests.

## Definition of done, mapped

| Requirement | Where it is proven |
|---|---|
| Notebooks in order give forecasts, gaps and 5+ pending transfers; forecaster beats both baselines | `09_verify` (build mode); `databricks/tests/test_core.py` |
| A planner sees today's summary and approves two transfers; data shows approved with audit rows; double-approve harmless; a viewer cannot approve | `e2e/flows.spec.ts`; `backend/tests/test_approvals.py` |
| Ask answers 10 sample questions and cannot modify data | `make smoke` |
| No secrets in repo, logs or browser; no string-built SQL; no banned words in the UI | no secrets exist to store; `test_sql.py`; `app.test.tsx` and `flows.spec.ts` |
| Runs in sample mode with one command, live mode after configuration | `make dev`; `infra/.env.example` |
