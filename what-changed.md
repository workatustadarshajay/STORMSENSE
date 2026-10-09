# What changed

This log covers the work done after the scoring criteria were shared (alignment to Databricks features 30%, novelty 30%, demo 10%, business impact 20%, presentation and Q&A 10%). Earlier build work is summarised in `contect.md`.

Status key: **Verified** means run on the Databricks workspace or tested. **Built, not verified** means the code exists but was not run end to end. **Blocked** means it cannot reach users yet.

---

## 1. Databricks features added

### 1.1 Lakeflow Declarative Pipeline: data-quality gates (Verified)
- New: `databricks/pipelines/data_quality.sql`. It defines three materialized views: `sales_clean`, `weather_observed_clean` and `inventory_clean`.
- Nine expectations: rows with negative units, negative stock, negative rain or wind, or a missing date are dropped. An implausible temperature (outside -40 to 135°F) fails the run.
- New bundle resource: `databricks/resources/pipeline.yml` (`StormSense - Data quality gates`, serverless).
- Wired into both jobs: the build job runs it after sample data; the daily job runs it before features.
- The features step now reads `sales_clean` and `weather_observed_clean`. The gaps step reads `inventory_clean`.
- Result: all nine expectations passed on every row (zero failures).

### 1.2 AI/BI (Lakeview) dashboard: `StormSense overview` (Built, deployed, not visually checked)
- New generator: `databricks/scripts/make_dashboard.py`, which writes `databricks/dashboards/stormsense_overview.lvdash.json`.
- New bundle resource: `databricks/resources/dashboard.yml`.
- Contents: counters for urgent transfers, transfers waiting, sales protected, and stores running low; bar charts for units short by store, units expected by product and DBUs per day; tables for forecast accuracy and transfers waiting.
- Its queries return live data. The layout has not been opened in a browser.

### 1.3 Cost tracking: `workspace.stormsense.cost_daily` (Built, no data yet)
- New notebook: `databricks/notebooks/11_cost_view.py`. It creates a view over `system.billing.usage`, filtered to usage from jobs tagged `project: stormsense`, with an estimated dollar figure at list price.
- All three jobs now carry the tag `project: stormsense`.
- The build job runs the view as its final task.
- Status: 0 rows. Billing data lags by hours, and the dollar figure stays blank when list prices are not published for this region. Re-check later.

### 1.4 AI agent: Storm desk (Built and tested live; not deployed)
- Backend: `backend/app/agent.py`. A tool-calling loop over four read-only tools: overview, stock risks, pending transfers, and a store's 7-day forecast.
- Model: `databricks-gpt-5-mini` through the serving endpoint, called over REST because the SDK's `query` method in this version does not accept tools. Configurable with `STORMSENSE_AGENT_MODEL`.
- API: `POST /api/storm-desk`, rate-limited to 5 requests per minute per person, with the same request-header protection as other write-style endpoints.
- Frontend: new page `frontend/src/pages/StormDesk.tsx` at `/storm-desk`, linked from the Transfers screen. Shows the plan, the transfers it refers to, and a list of the checks it made.
- Guardrails:
  - No write tools exist.
  - A plan may only name transfer IDs that a tool returned in the same conversation.
  - At most six tool steps.
  - Technical words are removed from the output.
  - The planner's goal is treated as data, not as rules.
- Tests: 9 agent and API tests (scripted model), 5 page tests, plus the browser suite.
- Live: two goals and one stock question were run against the real model and tables. Two of the plans cited real transfer IDs. Two quantities (53 and 44 units) match the table; the Texas heat-wave dates also match.

---

## 2. Changes to existing features

| Area | Change | Why |
|---|---|---|
| Model | Retrained by the build run: now champion v3, WAPE 0.391 (was v2, 0.403). Promoted because it beats both baselines (0.667 and 0.571). | Normal retraining on the regenerated data. |
| Sample data | Regenerated for the new date, so history now ends October 8 and a new stock snapshot exists. | The workflow runs on the current date. |
| Forecast table | Contains October 7 and October 8 rows. The October 7 rows are stale and have not been removed. | Replacing old rows needs your approval. The app and dashboard only read the latest date. |
| App bundle | The app environment variables use `value_from` (the bundle file was ignored with `valueFrom`). `app.yaml` keeps `valueFrom`. | Found in the real deploy output. |
| Web build | Fonts are embedded in the stylesheet, and the favicon is inline. The only build files are HTML, JS and CSS. | The workspace refuses binary font files in an app bundle. |
| Web app | Focus no longer jumps to the main area on the first page load. | Found by browser testing. |
| Ask | Answers are cut to one plain sentence, with markdown removed and long answers shortened. | Genie answers contained markdown and lists. |
| Approvals | The skipped-attempt audit insert uses a form Databricks accepts (`uuid()` moved into the select). | The live repeat-approval test failed before this fix. |
| Integer parameters | Small integers are bound as `INT` so `LIMIT` works. | Live query failure found on the workspace. |
| Dev commands | `make dev` uses the workspace when `backend/.env` exists; `make dev-sample` uses sample data. The API logs which data it is using. | Lets you run against real data by default. |
| Test identity | Browser tests pin their own test user, so they don't depend on a local `.env`. | Prevents local settings leaking into tests. |
| Architecture site | Status panel text reflects only verified items. | Accuracy. |

---

## 3. Blocked or not yet done

- **Databricks App deployment: Blocked.** The company web filter (Zscaler) rejects the upload of `backend/app/service.py`, with a "blocked in accordance with the internet usage policy" page. This happens with plain `curl` too, and it is not a Databricks permission issue. Options are in `contect.md`, section 7. The app runs locally against the workspace in the meantime.
- **Grants job (`stormsense_app_access`):** not run, because it needs the app's service principal.
- **Storm desk in the deployed app:** unavailable until the app is deployed.
- **Dashboard visual check:** not opened in a browser yet.
- **Cost view:** no rows yet.
- **GitHub Pages architecture site:** built locally in `../STORMSENSE-architecture`, not pushed. The empty public repo has to be created first.
- **Git:** nothing from this build is committed to the main repository. Commits happen only when requested.

---

## 4. Files added since the scoring criteria

- `databricks/pipelines/data_quality.sql`
- `databricks/resources/pipeline.yml`
- `databricks/resources/dashboard.yml`
- `databricks/dashboards/stormsense_overview.lvdash.json`
- `databricks/scripts/make_dashboard.py`
- `databricks/notebooks/11_cost_view.py`
- `backend/app/agent.py`
- `backend/tests/test_agent.py`
- `frontend/src/pages/StormDesk.tsx`
- `frontend/src/test/storm-desk.test.tsx`
- `docs/running-locally.md` (updated: Storm desk section, Ask space ID)
- `what-changed.md` (this file)

Files changed since the scoring criteria, besides those above: `databricks/databricks.yml`, `databricks/resources/jobs.yml`, `databricks/notebooks/03_features.py`, `databricks/notebooks/07_gaps.py`, `backend/app/api.py`, `backend/app/main.py`, `backend/app/config.py`, `backend/app/schemas.py`, `backend/app/dbx.py`, `backend/app/sources/databricks.py`, `backend/app/service.py`, `backend/databricks.yml`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/src/api/hooks.ts`, `frontend/src/api/schema.d.ts`, `frontend/src/pages/Transfers.tsx`, `frontend/src/components/Shell.tsx`, `frontend/e2e/flows.spec.ts`, `frontend/playwright.config.ts`, `frontend/vite.config.ts`, `frontend/index.html`, `Makefile`, `contect.md`, `docs/architecture/index.html`, `docs/runbook.md`.
