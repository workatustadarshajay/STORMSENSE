# StormSense: full context for any agent

Written 2026-10-08 at the end of a long build session. Read this first, then `README.md` and `docs/`. It is meant to be pasted into or loaded by any coding agent that continues the work. It holds no secrets: authentication is an OAuth profile in the CLI, never a token in a file.

(The filename keeps the owner's spelling, `contect.md`.)

---

## 1. What this is

**StormSense** is a weather-driven demand forecasting and store-to-store inventory transfer system for a home-improvement retailer. Every morning it answers one question for a planner: *given the weather coming this week, which stores will run short, which have extra, and what should move where?* Planners approve or reject the moves on a phone or laptop.

Scope: 10 stores in 3 regions (Florida, Texas, California), 5 products (1000W generator, 4x8 plywood sheet, 20x30 tarp, submersible pump, 120-quart cooler), 12 months of daily history, 7-day forecast horizon. The data is **generated sample data** (no real retail feeds exist yet); the UI labels it "Sample data".

Three layers: **Databricks** (Delta tables in Unity Catalog, serverless notebooks, MLflow, Workflows, Genie), a **FastAPI** gatekeeper (the only thing that talks to Databricks), and a **React** web app (planners; talks only to the API).

## 2. Rules and preferences the owner has set (follow these)

* **Never write "PoC", "proof of concept", "prototype" or "demo-only" anywhere** in code, UI, docs, commits, job descriptions or Databricks object comments. It must read as a finished professional product. (Sample data is still honestly labelled "sample data": that is a data label, not a PoC label.)
* **Create everything in Databricks from code** (CLI, SDK, Declarative Automation Bundles), never by clicking in the UI.
* **Connect to the real Databricks data**, not fixtures, whenever the owner runs the app. `make dev` does this when `backend/.env` exists.
* **Planners are non-technical.** These words must never appear in the UI (a test enforces it): SQL, Delta, Databricks, Genie, MLflow, warehouse, SKU, MAPE, WAPE, model, API. Use: product, store, forecast, running low, extra stock, move, approve.
* Never invent metrics, customers, testimonials or ROI. Anything shown must come from the data or be labelled sample data.
* No secrets in code, git, logs or the browser. Every SQL statement must use bound parameters.
* **Commit or push only when the owner asks.** Nothing from this build is committed to the main repo yet (see section 9).
* **Confirm before billable or outward-facing actions** (deploying an app, creating public repositories). Running serverless jobs for verification was authorized.
* **Do not circumvent security controls** (see the proxy finding in section 7).
* Be honest about what is verified and what is not. The owner is intolerant of "works" claims that were not actually run.
* Style: short plain sentences, no filler. The owner interrupts often with new requests mid-task; handle them without losing the thread.

## 3. Current state at a glance

| Area | State |
|---|---|
| Databricks connection | Working. OAuth profile `stormsense`. |
| Delta tables / Unity Catalog | 15 tables in `workspace.stormsense`, filled. |
| Serverless notebooks | 10 notebooks. The first nine (setup through verify) ran green on the workspace; the tenth (grants) has not run yet because it needs the app's service principal. |
| MLflow + model registry | Experiment `/Shared/stormsense-demand-forecast`; `workspace.stormsense.demand_forecaster` v1 and v2, alias `champion` = **v2**. |
| Workflows | 3 jobs deployed and **run successfully**: build (twice), daily (once, all 6 tasks), app-access (never run, needs the app). Daily schedule is live. |
| Genie (Ask space) | Created from code, id `01f1c2f5ca641bd5b2e7ccbfe66fd3dc`. Answers 10 of 10 sample questions correctly on real data; cannot change data. |
| API + web app | Working locally against the real workspace (`make dev`), including real approvals. |
| **Databricks App (hosting)** | **NOT deployed.** Blocked: the company web proxy rejects the upload of one file (`backend/app/service.py`). See section 7. No app exists in the workspace. |
| New architecture site on GitHub Pages | Built and committed locally in `../STORMSENSE-architecture`; **not pushed**: the empty GitHub repo has to be created by the owner. |
| Main repo git | Nothing committed (26 untracked or modified paths on `main`; last commit `fab4672`). |

## 4. Environment (the dev box)

* Remote Linux box (VS Code remote), user home `/home/308638@USTDEV.COM`, project at `~/Projects/STORMSENSE`. No sudo.
* **Behind a company web proxy (Zscaler).** It re-signs TLS. Consequences:
  * `uv`: use `uv pip install --system-certs ...`.
  * npm works; Playwright browser download needs `NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt`.
  * **Python (Databricks SDK) hangs silently for minutes** unless `REQUESTS_CA_BUNDLE` and `SSL_CERT_FILE` point at `/etc/ssl/certs/ca-certificates.crt`. The `Makefile` exports them automatically; export them yourself for ad-hoc scripts.
* Python 3.12 virtualenv at `.venv` (pandas pinned `<3` to match the serverless runtime). Node 24 locally (CI uses 22). Playwright Chromium is installed in `~/.cache/ms-playwright`.
* Databricks CLI v1.20.0 at `~/.local/bin/databricks`. **Always pass `--profile stormsense`** (never rely on a default profile; the skills forbid auto-selecting one). OAuth only, never a personal access token.
* **Signing in on this box:** the OAuth callback is `localhost:8020` on the remote box, which the owner's browser cannot reach. Run `databricks auth login --host <url> --profile stormsense --debug` in the background (the link is in the debug log). If the browser cannot reach the callback, the owner pastes the failed redirect URL (`http://localhost:8020/?code=...&state=...`) and you `curl` it to `http://localhost:8020/` from the box. The authorization code is one-time and bound to a key that stays on the box.
* **Shell pitfall:** never `pkill -f '<text that appears in your own command>'`; it kills your own shell (exit 144). Use `kill $(pgrep -f "[u]vicorn app.main")` (bracket trick) or `fuser -k 8000/tcp`.
* Foreground `sleep` is blocked in the agent harness; use a background command or the Monitor tool.
* Genie, MLflow and job tasks take minutes; run them in the background and watch task state with `databricks jobs get-run <id> -o json`.

## 5. The Databricks workspace (identifiers are not secrets)

| Thing | Value |
|---|---|
| Host | `https://dbc-36f10c27-114c.cloud.databricks.com` (AWS, workspace id `7474643913319461`). Serverless only; looks like a Free Edition-style workspace. |
| CLI profile | `stormsense` (signed in as a workspace admin; run `databricks current-user me --profile stormsense`) |
| Catalog / schema | `workspace` (the default catalog) / `stormsense` |
| SQL warehouse | `Serverless Starter Warehouse`, id `52140806e6c8212a`, Small, auto-stop 10 min |
| Model | `workspace.stormsense.demand_forecaster`, alias `champion` -> v2 |
| MLflow experiment | `/Shared/stormsense-demand-forecast` (id `1582136179649889`) |
| Jobs | build `511985717262282`, daily `790663357420555` (cron `0 0 6 * * ?`, America/New_York, UNPAUSED, emails the deploying user on failure), app access `185697461473687` |
| Genie space | "StormSense Ask", id `01f1c2f5ca641bd5b2e7ccbfe66fd3dc`, over 8 tables |
| Bundle roots in the workspace | `/Workspace/Users/<user>/.bundle/stormsense-data/default` (complete) and `.../stormsense-app/default` (partial, from failed uploads) |

Tables in `workspace.stormsense` (see `docs/data-dictionary.md`, generated from `databricks/stormsense_core/tables.py`): `stores, products, settings, weather_observed, weather_forecast, sales_history, inventory_snapshot, features, predictions, forecast_intervals, model_runs, inventory_gaps, transfer_recommendations, transfer_audit, app_users`.

Current data (as_of = latest stock date 2026-10-07): 350 forecasts (10 stores x 5 products x 7 days), 50 stock rows (23 balanced, 11 shortage, 16 surplus), 13 pending transfers (4 urgent, about $54k of sales protected), 0 decided, 0 audit rows, 1 weather issue (100 rows). The owner's workspace user is in `app_users` as `admin`.

## 6. Repository map and how things work

```
(bundles)                 data bundle: databricks/databricks.yml; app bundle: backend/databricks.yml; no bundle file at the repo root
databricks/
  stormsense_core/        shared pandas library: reference, synth (sample data), weather (+NWS adapter), features,
                          model (HistGradientBoosting, Poisson), planning (gaps + transfers), tables (DDL + dictionary), dbx (Spark I/O)
  notebooks/01..10        source-format notebooks (setup, sample_data, features, train_register, refresh_weather,
                          score, gaps, recommendations, verify, grants). Import the library via the notebook path.
  resources/jobs.yml      build, daily, app_access workflows (serverless, environment client "4")
  scripts/                create_genie_space.py (idempotent), make_fixtures.py (writes backend/app/fixtures.json)
  tests/                  16 library tests
backend/
  app/                    FastAPI: main, api, service, auth, security, config, schemas, dbx (warehouse client),
                          sources/{base,databricks,mock}.py, fixtures.json (sample data for mock mode)
  databricks.yml, app.yaml   the Databricks App definition
  scripts/                smoke.py (live check), export_openapi.py
  tests/                  47 tests (contract, approvals, SQL parameterization, warehouse client, security)
frontend/                 React 18 + TypeScript + Vite + Tailwind 4 + React Router + TanStack Query; types generated from the API
                          src/{pages,components,api,lib,test}, e2e/ (Playwright), 25 unit tests, 23 browser tests
infra/                    deploy.sh (creates everything), build_architecture_site.py, Dockerfile + compose (never built), .env.example
docs/                     architecture.md, forecasting.md, runbook.md, running-locally.md, go-live.md, how-to-verify.md,
                          demo-script.md, data-dictionary.md (generated), architecture/ (the 5-diagram website, see below)
src/, index.html          the public marketing landing page (separate; deployed to GitHub Pages by .github/workflows/deploy.yml)
.github/workflows/        deploy.yml (landing page), ci.yml (lint, tests, contract check, browser tests; never run, not pushed)
.github/skills/           reference skills the owner supplied (databricks-*, frontend-design, design-handoff, archify, ...)
Makefile                  `make help` lists everything
```

**Daily cycle (job at 6:00 AM Eastern):** refresh weather -> features -> score (loads `champion` by alias) -> gaps -> recommendations (MERGE into PENDING rows only) -> verify. Idempotent; verified by running it more than once.

**API (all under `/api`):** `health` (`?deep=true` checks the warehouse), `me`, `overview`, `transfers` (+ detail), `transfers/approve`, `transfers/reject`, `stores`, `stores/{id}/forecast`, `inventory`, `history`, `ask`. State-changing posts require the header `X-Requested-With: stormsense`.

**Key design decisions (and deviations from the owner's original plan):**
* Hosting is a **Databricks App** with workspace sign-in (`X-Forwarded-Email` header set by the platform proxy) and roles from the `app_users` table, **instead of** the plan's email/password + JWT + Postgres. A local dev identity (`STORMSENSE_DEV_USER_EMAIL`) exists only when `STORMSENSE_ENVIRONMENT=local`.
* Model: scikit-learn `HistGradientBoostingRegressor` (Poisson loss) instead of LightGBM (same family, preinstalled on serverless). AutoML is not used (deprecated).
* Features are lagged by the 7-day horizon (no leakage); historical weather gets forecast-sized noise; validation is the last 28 days (time split). The model is promoted to `champion` only if it beats both baselines ("same as last week", "trailing 28-day average") on WAPE. Real result: WAPE 0.403 vs 0.667 and 0.571.
* Uncertainty: per-product 10th/90th percentile of weekly actual/forecast ratios (`forecast_intervals`). Transfer confidence = shortfall at P10 / shortfall at P50 (>=0.7 High, >=0.4 Medium).
* Approvals: `UPDATE ... WHERE status='PENDING'` stamps a request id on the rows it changed; `SELECT` by request id gives exactly what changed; audit rows for changes and for skipped attempts. Verified live.
* Two bundles (data first, then Ask space, then app) so the app can be given the space id.
* The Ask answer is cleaned to one plain sentence plus a table (Genie returns markdown and lists).
* Mock mode (fixtures made by the same library) exists so everything runs with no workspace; fixtures shift by whole weeks so weekdays stay correct.

## 7. Verified, and what is blocked

**Verified by actually running it (not assumed):**
* All notebooks and the three-stage pipeline on serverless; build job twice, daily job once; row counts stable (idempotent).
* MLflow run and UC model registration with alias; metrics identical to local training.
* `databricks/scripts/make_fixtures.py`, local tests: 16 library + 47 backend Python tests, 25 web unit tests, 23 browser tests (desktop and phone, axe accessibility scan, CSP/console errors, two-people-approve-the-same-transfer), lint and type checks clean.
* `make dev` serves real workspace data through the real UI. Real approve + repeat on the real tables worked (after fixes below); the test transfer was restored to PENDING and the two test audit rows were deleted (audit table was empty before and after).
* `backend/scripts/smoke.py` against the live workspace: 9/9 checks, including Ask 10/10 and "Ask cannot change data".
* The first three stages of `infra/deploy.sh` (bundle deploy + build job + Ask space) ran end to end via `make deploy`.

**Blocked: deploying the Databricks App.** `databricks bundle deploy` in `backend/` fails with "access denied: possible permission error". The real cause is **not Databricks**: the response body is the company web filter's block page ("This website is blocked in accordance with the UST Internet Usage Policy"). Uploading `backend/app/service.py` through `workspace-files/import-file` returns 403 **every time** (reproduced with plain curl); the other 16 app files upload fine when sent one at a time (the CLI's parallel bursts were also being refused at random). `service.py` is a normal Python file; the trigger is unknown. **Do not try to hide or reshape the file to slip past the filter**: that is a security control and needs the owner's decision.
Options to offer the owner: (1) ask the network/security team to allow it; (2) deploy from CI (GitHub Actions) or another network using a Databricks service principal; (3) have Databricks pull the code server-side from a Git folder (requires pushing the code to GitHub, which publishes it if the repo is public); (4) keep running locally against the workspace, which already works. After the files go through: `make deploy` (or `cd backend && databricks bundle deploy --var warehouse_id=... --var genie_space_id=... && databricks bundle run stormsense`), then the app-access job with the app's service principal, then `make smoke`.

**Not yet verified:** the `stormsense_app_access` (grants) job (needs the app's service principal), the deployed app itself, `infra/deploy.sh` steps 4 to 6, the Docker image (never built; the owner stopped that step), GitHub Actions CI, live NWS weather inside the job (the adapter was tested against the live NWS API locally; the job default is the `sample` provider), `delete`/re-create scenarios.

## 8. Bugs found along the way (do not reintroduce)

1. SQL table comments with apostrophes broke `CREATE TABLE` (escape with backslash; test added).
2. Writing pandas to Delta must pass the table's exact Spark schema (`INT` vs inferred `BIGINT` fails; `Ctx.frame` does it).
3. Serverless auto-retries deterministic failures; the build job sets `disable_auto_optimization`.
4. `LIMIT :n` rejects a `BIGINT` parameter: ints that fit bind as `INT`.
5. `uuid()` is not allowed inside a `VALUES` list: use `INSERT ... SELECT uuid(), ... FROM VALUES ... AS t(rec_id)`. (Fake-database tests could not catch 4 and 5; only the live run did.)
6. React: an effect that returns `scrollIntoView(...)` crashes in current Chromium (it returns a Promise); wrap in braces.
7. CSP `font-src` must allow `data:` because fonts are embedded (the workspace also refuses binary font files in an app bundle, so Vite inlines them: `assetsInlineLimit`).
8. Bundle `config.env` entries need `value_from` (snake_case); `app.yaml` uses `valueFrom`.
9. Genie answers contain markdown and lists: cleaned in `plain_sentence`.
10. The local `backend/.env` identity must not leak into tests or sample mode (pinned in `playwright.config.ts` and `make dev-sample`).
11. The Ask space id must be in `backend/.env` (`DATABRICKS_GENIE_SPACE_ID`), otherwise Ask says "Questions aren't available right now".
12. Python SDK hangs behind the proxy without `REQUESTS_CA_BUNDLE` (section 4).

## 9. Open items and next steps

1. **Decide how to deploy the app** (section 7), then deploy, run the grants job, run `make smoke`, update the status panel in `docs/architecture/index.html`, rebuild the standalone site.
2. **Publish the architecture site as its own GitHub Pages site.** The owner asked for the 5 diagrams plus hub to be a separate Pages site "like the existing demo page". One repo hosts one Pages site, so it needs a new repo. This box has no `gh` CLI or token, but SSH is authenticated as the owner's GitHub account (`git@github.com`), so a push works once the **empty repo exists**. Suggested: `STORMSENSE-architecture`, public (`https://github.com/new?name=STORMSENSE-architecture&visibility=public`). Local repo is ready at `../STORMSENSE-architecture` (2 commits, workflow `.github/workflows/pages.yml`, site in `site/`). Then: `git remote add origin git@github.com:workatustadarshajay/STORMSENSE-architecture.git && git push -u origin main`, and in the repo's Settings > Pages set Source to GitHub Actions. Rebuild the folder any time with `python infra/build_architecture_site.py ../STORMSENSE-architecture`.
3. Commit the main repo when asked (everything is untracked). Commit messages from this assistant end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
4. Optional: lower the warehouse auto-stop, real feeds (`docs/go-live.md`), live weather (`--var weather_provider=nws`), a CI run on GitHub once pushed.

## 10. Architecture website

`docs/architecture/index.html` is a hub (left rail, status panel, embedded diagrams) over five interactive diagrams generated with the Archify skill from JSON in `docs/architecture/src/` (system, daily pipeline, approving a transfer, transfer lifecycle, deploying). All five passed Archify's four gates (validate, deliver, check, real-browser check). They are **not pinned to a commit** (the code is uncommitted, so repository evidence could not be attached). Regenerate with `make architecture` (set `ARCHIFY_CHROME` to a Chrome binary, for example the Playwright one). The generated pages have two accessibility findings of their own (heading order, nested interactive SVG controls) that live inside Archify's viewer, not in StormSense code; the hub page itself scans clean.

## 11. Commands you will need

```bash
make setup                      # venv + web dependencies
make dev                        # REAL data if backend/.env exists (API :8000, web :5173)
make dev-sample                 # fixtures, no workspace
make test && make lint          # 63 Python + 25 web tests
make e2e                        # browser tests, always sample data (they approve transfers)
make smoke WAREHOUSE_ID=52140806e6c8212a SPACE_ID=01f1c2f5ca641bd5b2e7ccbfe66fd3dc
make deploy                     # everything in the workspace; asks first, YES=1 skips the prompt
make pause | make resume        # the 6:00 AM schedule
make architecture               # regenerate the five diagrams
databricks bundle run stormsense_daily --profile stormsense      # run the daily cycle now
```

`backend/.env` for live local runs holds: `STORMSENSE_MODE=databricks`, `STORMSENSE_DATABRICKS_PROFILE=stormsense`, `DATABRICKS_WAREHOUSE_ID`, `DATABRICKS_GENIE_SPACE_ID`, `STORMSENSE_CATALOG=workspace`, `STORMSENSE_SCHEMA=stormsense`, `STORMSENSE_DEV_USER_EMAIL` (the owner's workspace email). It is git-ignored.

**Live approvals are real writes.** To test and undo: approve one NORMAL transfer through the API, check `transfer_recommendations` and `transfer_audit`, then restore with `UPDATE ... SET status='PENDING', decided_by=NULL, decided_at=NULL, decision_note=NULL, decision_request_id=NULL WHERE rec_id='...'` and delete only the audit rows you created (look at them first).

## 12. The owner's original brief (condensed)

Build StormSense with milestones: (1) Databricks foundation and data: schema, dimensions, settings, a year of weather-driven sample data (named storm and heat events, a storm and heat wave in the upcoming forecast, deliberate shortage and surplus in the latest stock); (2) features and the forecaster (time split, leak-free, MLflow, beats two baselines, UC alias `champion`, intervals from validation residuals); (3) scoring, shortage/surplus, transfer recommendations (nearest source, spare-only, min quantity, max distance, urgent rules, plain-English reason, never overwrite non-PENDING rows, no duplicate pending); (4) a daily 6:00 AM job (refresh weather, features, score, gaps, recommendations, verification) on serverless with retries and failure email; (5) a FastAPI backend (service principal to Databricks, parameterized SQL, roles, guarded idempotent approvals with audit, friendly "getting things ready", cached overview, OpenAPI-generated frontend types, tests incl. SQL parameterization and approval idempotency, a live smoke script); (6) a React app for non-technical phone-first users (Today, Transfers, Store forecast, Ask, History; loading/empty/error states in plain language; accessibility; component and end-to-end tests including approve and double-approve); (7) packaging and docs (Docker, Compose, Makefile, CI, architecture, data dictionary, runbook, go-live checklist, demo script).
**Definition of done:** notebooks produce forecasts, gaps and at least five pending transfers with the model beating both baselines; a planner can approve two transfers with audit rows, double-approve is harmless, a viewer cannot approve; Ask answers 10 questions and cannot modify data; no secrets, no string-built SQL, no banned words in the UI; the app runs on sample data with one command and on real data after configuration.
**Do not:** use random sales unrelated to weather, a random split for time series, hardcoded confidence/accuracy/ROI, overwrite the recommendations table, call Databricks from the browser, use a personal access token in deployed code, depend on classic clusters or AutoML.
