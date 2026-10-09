# StormSense — feature backlog

What this file is: the result of a full pass over the running app, the Databricks
bundle, the API and the workspace, listing **what already exists**, **what is
missing**, and **every feature worth adding** — with who it helps, how much work
it is, what it depends on, and where in the code it lands.

It is a plan, not a claim.

> **Status check — 2026-10-09, after this catalogue was drafted.** Part of the plan
> below has since landed in the working tree from a parallel change set. I did not
> write it; I only re-read it and validated it.
>
> | Item | Landed as |
> | --- | --- |
> | **C1 + C6** | `databricks/pipelines/data_quality.sql` — `sales_clean`, `weather_observed_clean`, `inventory_clean` materialized views carrying `CONSTRAINT … EXPECT … ON VIOLATION DROP ROW` (and `FAIL UPDATE` for an implausible temperature); `databricks/resources/pipeline.yml` with `serverless: true`; wired as a **`data_quality` pipeline task in both jobs** (after `sample_data` in build, after `refresh_weather` in daily); `03_features.py` and `07_gaps.py` now read the `*_clean` views |
> | **B1** | `databricks/resources/dashboard.yml` + `databricks/dashboards/stormsense_overview.lvdash.json` |
> | **D1 / D2** | `databricks/notebooks/11_cost_view.py`, run as a `cost_view` task after `verify` in the build job |
> | **D3 (tagging half)** | `tags: {project: stormsense}` on all three jobs; a `warehouse_id` variable added to `databricks.yml`, and its `catalog` default changed from `""` to `workspace` |
>
> **What I verified:** `databricks bundle validate --profile stormsense` → `Validation OK!`,
> exit 0. That covers bundle structure, variable resolution, the job → pipeline
> reference and the dashboard's warehouse reference.
>
> **What is still unverified:** nothing has been deployed. The pipeline has never
> run, the dashboard has never rendered, and `11_cost_view.py` has never executed.
> C3 (Model Serving), C4 (monitoring), C5 (Auto Loader), E1 (Lakebase), and the
> whole A and F families are untouched. The marker ⚠ below means **written, not run**.

---

## 0. How this was produced

| Search | Method | Result |
| --- | --- | --- |
| App surface | `backend/app/api.py`, `frontend/src/App.tsx`, `frontend/src/{pages,components}` | 12 endpoints, 5 screens, 4 shared components |
| Data + jobs | `databricks/resources/jobs.yml`, `databricks/notebooks/*`, `stormsense_core/*` | 3 jobs, 15 tables, 10 notebooks at the time of the sweep (11 now — see the status check) |
| Docs | `README.md`, `docs/*.md` | 8 documents, all engineer-facing |
| UI text | `grep -riE "help\|tooltip\|onboard\|faq\|glossary" frontend/src` | **no matches** — no help surface exists |
| Workspace capabilities | `databricks` CLI v1.20.0, read-only (`* list`) | pipelines ✔ dashboards ✔ postgres/Lakebase ✔ data-quality ✔ serving ✔ |
| Real cost data | `system.billing.usage` on warehouse `52140806e6c8212a` | **83 rows, 31.91 DBUs, one day** — already usable |

Verified workspace facts that shape the plan:

- Warehouse `52140806e6c8212a` (Serverless Starter Warehouse, PRO, auto-stop 10 min) — the only one.
- `databricks apps list` is **empty**: the app has never been deployed (the network blocks one file upload).
- `databricks pipelines list-pipelines`, `dashboards list`, `postgres list-projects` all return `[]` — the APIs are enabled but nothing exists yet.
- `serving-endpoints list` shows only Databricks-hosted foundation-model endpoints; no custom endpoint.
- New CLI groups present: `data-quality` (Data Quality Monitoring, Public Preview), `pipelines`, `lakeview`, `dashboards`, `postgres`, `psql`, `quality-monitors`.
- Bundle resource types this CLI can deploy include `dashboards`, `pipelines`, `database_instances`, `postgres_branches`, `quality_monitors`, `model_serving_endpoints`, `apps`, `jobs`.
- System tables available: `system.access`, `system.ai`, `system.alert`, `system.billing`, `system.compute`, `system.lakeflow`, `system.mlflow`, `system.query`.

---

## 1. What already exists (do not rebuild)

**The decision loop.** `06_score` loads the champion by alias → `07_gaps` finds shortage/surplus → `08_recommendations` MERGEs ranked moves into `transfer_recommendations`, touching only `PENDING` rows. `09_verify` re-checks row counts. Six tasks at 6:00 AM Eastern.

**The proof.** 16 library + 47 API + 48 web tests, a 9-check live smoke script, WAPE 0.403 against 0.667/0.571 baselines.

**The planner surface.** `Today`, `Transfers`, `Stores` (forecast), `Ask`, `History` — phone-first, plain-language, role-gated, audited approvals.

**Databricks usage that is already real.** Unity Catalog (15 Delta tables), 10 serverless notebooks, MLflow + champion alias, three Lakeflow Jobs, a Genie Ask space, Declarative Automation Bundles, UC grants for the app's identity.

## 2. Gaps the search found

1. **No help or onboarding anywhere in the UI.** A planner who opens the app on day one has no in-product explanation of what "confidence" means, why a transfer is urgent, or what happens after they approve. The knowledge exists (`docs/demo-script.md`, `README.md`, `docs/forecasting.md`) but only in the repo.
2. **No visual answer for a non-technical stakeholder.** The reasoning lives in tables and a FastAPI JSON, not in a chart anyone can read in a room.
3. **The feed is imperative notebooks, not a declared pipeline.** No column-level expectations, so a bad weather row or a negative forecast is only caught by `09_verify` after the fact.
4. **Scoring is a job task, not a service.** Every model change needs a job run; the app cannot ask for a live score, and there is no clean promote/rollback step.
5. **Nobody watches accuracy over time.** WAPE is printed in a run log. Drift would surface as planners losing trust, not as an alert.
6. **Spend is invisible.** Real cost data sits in `system.billing.usage` and nobody looks at it — including the number the hackathon judges ask about (cost effectiveness).
7. **App state is stateless.** Approvals rely entirely on the warehouse; there is no fast store for per-user working state (a draft decision, a filter, the last question asked).
8. **Feeds are one-shot loads.** `02_sample_data` writes whole tables; real files landing in a volume have no incremental path.

---

## 3. The catalogue

Effort scale: **S** ≤ half a day, **M** ≈ 1–2 days, **L** ≥ 3 days.

### A. Help and onboarding — *the fastest visible win* — Effort **S**

| # | Feature | What it does |
| --- | --- | --- |
| A1 | **In-app Help page** (`/help`) | One screen, plain words: what the app answers, what each column means, what happens after you approve. Sections: *What this is*, *Reading a recommendation*, *Confidence & urgency*, *Approve vs reject*, *Who can do what*, *What to do if the list is empty*. |
| A2 | **Glossary drawer** | A slide-over defining the eight words a planner meets — forecast, running low, extra stock, move, confidence, urgent, protected sales, sample data. Reused as inline `?` popovers later. |
| A3 | **First-run tour on Today** | Three dismissible callouts on the first visit (persisted per user in `app_users` or `localStorage`), pointing at the headline numbers, the urgent card, and the nav. |
| A4 | **Empty/error copy pass** | Every `StateViews.tsx` state gets one plain sentence about what the planner should *do*, plus a link into Help. |
| A5 | **`docs/planner-guide.md`** | The same content as A1 as a printable one-pager for training sessions. |

**Why:** the strongest "overall quality" move available. Planners are explicitly non-technical and the repo rule forbids jargon in the UI — Help is where the jargon-free explanation belongs. It also gives the demo something to show after the video.
**Where:** `frontend/src/pages/Help.tsx` (new), `frontend/src/components/{Glossary,Tour}.tsx` (new), route + nav entry in `App.tsx` / `Shell.tsx`, copy in `docs/planner-guide.md`.
**Depends on:** nothing. Can ship today.

### B. Trust you can see — *demo + business impact* — Effort **S–M**

| # | Feature | What it does |
| --- | --- | --- |
| B1 | ⚠ **AI/BI (Lakeview) dashboard** | "Revenue protected, stores at risk, forecast accuracy" — the three numbers a room reacts to, on one page, filterable by region and product. |
| B2 | **Accuracy-over-time tile** | WAPE per run, one line per method, from `model_runs` — makes "measured, not asserted" visible instead of a log line. |
| B3 | **Run health strip** | Last daily run's status, duration and row counts from `system.lakeflow` + `09_verify` output. |
| B4 | **Ask follow-ups** | Pin a question, re-run it, and keep the last N answers per user. |

**Why:** B1/B2 carry Demo (10%) and Business impact (20%) at once; B2/B3 also feed "handling of Q&A" because every number is one click from its source.
**Where:** `databricks/resources/dashboard.yml` (new bundle resource — `dashboards` is a supported type), a `forecast_accuracy` gold table, `frontend/src/pages/History.tsx` for B4.
**Depends on:** B2's table existing before the dashboard can be honest.

### C. Databricks-native alignment — *30% criterion* — Effort **M–L**

| # | Feature | What it does |
| --- | --- | --- |
| C1 | ⚠ **Lakeflow Declarative Pipeline for the daily feed** | *What landed:* a three-view quality-gate pipeline (`sales_clean`, `weather_observed_clean`, `inventory_clean`) that both jobs now run as a task. *What is still open:* declaring `features`, `predictions` and `inventory_gaps` as SDP datasets so the pipeline owns the whole feed half, not just the gates in front of it. |
| C2 | **Keep the recommendation MERGE in the job** | `08_recommendations` stays a job task — SDP cannot express "update only PENDING, delete only PENDING-by-source". Documenting *why* is part of the alignment story. |
| C3 | **Model Serving endpoint for the champion** | Serve `stormsense.demand_forecaster@champion` as a real endpoint; `06_score` and the app call it instead of loading the model in-process. |
| C4 | **Lakehouse / Data Quality Monitoring on forecasts** | `data-quality create-monitor` over a `forecast_accuracy` table: drift and error tracked per run, with alerts. |
| C5 | **Auto Loader for real feeds** | `STREAM read_files(...)` over a UC Volume so landed sales/stock/weather files are ingested incrementally instead of whole-table writes. |
| C6 | ⚠ **Data-quality expectations on the feeds** | *What landed:* non-negative units / rain / wind / stock counts, no null keys on sales and stock dates, and a physically implausible temperature that fails the run. *What is still open:* `predicted_units >= 0` and weather rows covering the 7 days after the stock date — the two that guard the forecast itself rather than its inputs. |

**Why:** C1 + C6 are "built-in data quality, lineage and retries"; C3 and C4 are the two capabilities a Databricks judge expects to see used natively.
**Where:** `databricks/resources/pipeline.yml` + `databricks/pipelines/*.sql` (both landed; extend them for the open C1/C6 items), `databricks/notebooks/06_score.py` (call the endpoint for C3), `databricks/resources/monitor.yml` (new, C4), `databricks/stormsense_core/dbx.py` for C5.
**Modern API reminders** (from the repo's `databricks-pipelines` skill): SQL uses `CREATE OR REFRESH STREAMING TABLE` / `MATERIALIZED VIEW` with `CONSTRAINT … EXPECT (…) ON VIOLATION DROP ROW`; Python imports `from pyspark import pipelines as dp` (never `import dlt`); file ingest is `STREAM read_files(...)` — without `STREAM` a streaming table cannot be created. Incremental MV refresh needs serverless + Delta row tracking.

### D. Cost transparency — *business impact, with real numbers today* — Effort **S**

| # | Feature | What it does |
| --- | --- | --- |
| D1 | ⚠ **Spend-per-job view** | Daily DBUs and estimated USD per job/warehouse, straight from `system.billing.usage` joined to `list_prices`. |
| D2 | ⚠ **Cost-per-decision** | DBUs of the daily run ÷ transfers produced — the one cost number a business audience understands. |
| D3 | **Budget guardrail** *(job tags landed; the threshold warning did not)* | A threshold check after each run that warns when the day's DBUs exceed a set level. |

**Already measured (this workspace, one day of history):**

| Product | Job | DBUs |
| --- | --- | --- |
| GENIE | — | 13.835 |
| SQL | — | 12.056 |
| JOBS | `511985717262282` (build) | 2.945 |
| JOBS | `790663357420555` (daily) | 1.612 |
| DEFAULT_STORAGE | — | 0.967 |
| PREDICTIVE_OPTIMIZATION | — | 0.497 |

Total 31.91 DBUs. The daily cycle is **1.612 DBU** — a real, defensible number where a slide currently says "serverless, so it is cheap".

**Why:** turns the weakest slide claim into a screenshot. Also the honest way to answer "what will this cost at 500 stores?"
**Where:** `databricks/resources/dashboard.yml` (a Cost page) or a small `databricks/notebooks/11_cost.py` writing a `cost_daily` table; `system.billing.usage` needs no setup here — it is already populated.
**Depends on:** nothing, but note `list_prices` must be checked for actual prices before quoting USD; DBUs are verified today, dollars are not.
**Limit:** budget *policies* and policy tags are account-level console objects. A workspace admin cannot create them, so D3 is a query-and-warn, not a policy.

### E. Production readiness — Effort **L**

| # | Feature | What it does |
| --- | --- | --- |
| E1 | **Lakebase for app state** | Postgres for fast, per-user working state: draft decisions, saved Ask questions, dismissed tours, last-seen run. Keeps the warehouse for analytics and stops the app writing UI state into Delta. |
| E2 | **Connection-pooled reads** | Move the hot "Today" query behind a cache in Lakebase before it hits the warehouse. |
| E3 | **Audit export job** | Weekly parcel of `transfer_audit` to a volume, per `docs/go-live.md`. |
| E4 | **Alerting** | Failure email to a shared mailbox, plus an alert on `model_runs` when the forecaster stops beating the baselines. |

**Why:** E1 is the "production readiness" item on the alignment list; E4 is already on the go-live checklist and is pure Q&A insurance.
**Where:** `databricks/resources/postgres_project.yml` (bundle type `postgres_branches`/projects is supported), `backend/app/sources/lakebase.py` (new, behind the existing `DataSource` Protocol), `backend/app/config.py` (connection URL as an env var).
**Depends on:** a Lakebase project being provisioned (`databricks postgres list-projects` is currently empty). Keep it behind the `DataSource` seam so `mock` mode and tests stay unchanged.

### F. Product depth — Effort **M**

| # | Feature | What it does |
| --- | --- | --- |
| F1 | **"Why this move?" expander** | The `reason` field is one sentence; add the three inputs behind it (forecast, current stock, spare at source) so a planner can audit a single recommendation without leaving the card. |
| F2 | **Adjust a recommended quantity** | Let a planner approve a smaller quantity than recommended, recorded in `transfer_audit` with the original. |
| F3 | **Store-level what-if** | On `Stores`, slide a day's demand ±20% and see the run-low date move. Teaches the model's sensitivity without exposing it. |
| F4 | **Snooze instead of reject** | "Not this week" as a third outcome, so rejection stops meaning "the model is wrong". |
| F5 | **Weekly email digest** | A short Monday summary for planners who will not open an app. |
| F6 | **Multi-region scale story** | Nothing to build — a `settings`-driven dimension expansion, worth stating as a scale test. |

**Why:** F1 and F2 are the two things a planner will ask for in the first week of real use.

---

## 4. Suggested sequence

**Wave 1 — visible and cheap (no new infrastructure, no billing risk).**
A1–A5 (Help + glossary + tour), B2 (accuracy table + tile), D1/D2 (cost view from `system.billing`).
*Why first:* every one of these is verifiable locally, costs nothing to run, and each maps to a scoring criterion. A1 in particular is the only item that improves the app for its actual users rather than for the judges.

**Wave 2 — the Databricks story.**
C1 + C6 (SDP feed with expectations), C4 (monitoring on forecasts), B1 (Lakeview dashboard over the new gold tables).
*Why second:* needs a pipeline to exist before a monitor or dashboard can point at it. Watch out: C1 must not swallow C2 — the PENDING-only MERGE stays in the job.

**Wave 3 — cost and production readiness, only with a decision on spend.**
C3 (Model Serving), E1 (Lakebase), C5 (Auto Loader over a real feed).
*Why last:* C3 bills while it runs, E1 needs provisioning, C5 needs files that do not exist yet.

---

## 5. Honest constraints (say these out loud in Q&A)

- **The app is not deployed.** `databricks apps list` is empty; the network's upload filter refuses one file (`backend/app/service.py`). Waves 1–2 can be built and verified *locally against the real workspace*; the hosted screenshots do not exist yet.
- **Model Serving bills while running** and its entitlement on this workspace is unconfirmed — the only custom endpoint would be the first one created here. Confirm before committing, and prefer scale-to-zero if offered.
- **Verified vs assumed:** DBUs above are real. Dollars need `list_prices`. Lakebase's API answers but no project exists, so provisioning time is unknown. Lakeview dashboards and pipelines have working APIs but nothing has been deployed through them yet.
- **The one-day billing window** (2026-10-08 only) means cost trends need a few more days of runs before they mean anything.

## 6. How this maps to the scoring

| Criterion | Weight | Carried by |
| --- | --- | --- |
| Alignment to Databricks features | 30% | C1, C3, C4, C5, E1, plus what already exists (UC, MLflow, Workflows, Genie, Bundles) |
| Novelty of the idea | 30% | B1 + B2 (measured accuracy made visible), D2 (cost per decision), F1/F3 |
| Demo | 10% | A1 (Help), B1 (dashboard), C3 (live scoring from the app) |
| Business impact | 20% | D1/D2/D3 with real DBUs, plus the existing `~$54k` protected-sales figure |
| Overall quality / Q&A | 10% | A1–A5, B3, E4, and section 5 answered honestly |

## 7. Cheapest path to the biggest score movement

Two of the three are now written but unproven (C1+C6, D1 — see the status check),
so the remaining work is: **run them**, then build **A1 (Help page)**.

The order matters. C1+C6 and D1 exist as code and will not count for anything until
the pipeline has executed once with a green quality result and `11_cost_view.py`
has produced an actual table — a validator passing is not a pipeline working.
After that, A1 is the only item that improves the app for its actual users rather
than for the judges, and it is still the cheapest unused win in the catalogue.

A1 is also the one item left that touches a weighted bucket nothing else reaches:
every other family speaks to alignment, novelty or business impact, while Help is
the whole of the day-one experience for a non-technical planner.
