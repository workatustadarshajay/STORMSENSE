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
- Changed in section 5: `databricks/stormsense_core/weather.py`, `databricks/notebooks/05_refresh_weather.py`, `databricks/databricks.yml`, `databricks/tests/test_core.py`

Files changed since the scoring criteria, besides those above: `databricks/databricks.yml`, `databricks/resources/jobs.yml`, `databricks/notebooks/03_features.py`, `databricks/notebooks/07_gaps.py`, `backend/app/api.py`, `backend/app/main.py`, `backend/app/config.py`, `backend/app/schemas.py`, `backend/app/dbx.py`, `backend/app/sources/databricks.py`, `backend/app/service.py`, `backend/databricks.yml`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/src/api/hooks.ts`, `frontend/src/api/schema.d.ts`, `frontend/src/pages/Transfers.tsx`, `frontend/src/components/Shell.tsx`, `frontend/e2e/flows.spec.ts`, `frontend/playwright.config.ts`, `frontend/vite.config.ts`, `frontend/index.html`, `Makefile`, `contect.md`, `docs/architecture/index.html`, `docs/runbook.md`.

---

## 5. Real weather in the daily job (idea 4) (Verified)

- The daily job now uses the live US National Weather Service forecast by default (bundle variable `weather_provider`, notebook `05_refresh_weather`). `sample` is still available.
- Bug found and fixed before deploying: forecast days were grouped by UTC. An evening storm in Florida would fall on the next day. Days now use each store's own time zone. Regression test added (`test_nws_days_are_store_local_not_utc`).
- Verified: the daily job ran end to end on serverless, all seven tasks succeeded, including `refresh_weather` against the live service. All 10 stores have a full week of forecast days (October 9 to 15).
- Result for this week: the live forecast has **no storm, heavy-rain or heat alerts** (65 clear and 7 light-rain store-days; highest wind 29.9 mph). The sample storm and heat events from the earlier demo are no longer in the forecast. The Florida and Texas plans in the demo depend on which weather the day brings.
- The sales and stock figures are still sample data, so the app keeps its "Sample data" label.
- Demo implication: a live storm is needed for a dramatic demo. The what-if simulator (idea 1) would let a planner create one on demand.

---

## 6. Three new features: what-if simulator, feedback loop, crew (ideas 1 to 3)

### 6.1 What-if storm simulator (Built and verified on the workspace)
- Planner picks storm strength (0 to 100), when it hits, how many days, and which region. The simulator shows the normal week against the storm week, the sales lost if nothing moves (in dollars), and the stock that would need to move.
- Model Serving: the forecaster is served from a scale-to-zero endpoint, `stormsense-forecaster`. It scored 350 live feature rows. The endpoint bills only while it is running.
- Delta time travel: compares the stock plan saved before the last daily run with the plan now. Verified: 11 stores with a shortage before live weather, 9 after (652 units short before, 184 after).
- Nothing is written. Estimates only; the page says so.
- Code: `backend/app/whatif.py`, `POST /api/what-if`, `frontend/src/pages/WhatIf.tsx` (route `/what-if`, linked from Transfers). Tests: 7 backend simulator tests, 4 page tests.
- Caveat: the scenario's effect on lead-time weather is approximated over the days the feature table covers.

### 6.2 Feedback loop (Built and verified on the workspace)
- The reject dialog now requires a reason: no truck free, store closed, already covered, route too slow, or something else. Stored in the new table `rejection_feedback`.
- New notebook `12_learn_from_feedback`: each route gets a penalty from its recent rejections. Recent rejections count more (weight halves every 14 days) and drop out after 60 days.
- Recommendations rank a penalised route lower, and the reason says why ("Ranked lower: planners rejected a move on this route ... (last reason: truck unavailable)"). Learning never adds or removes a move.
- Added to both jobs, before the recommendations step.
- Tests: penalty ranking, decay window, and the "only route" case that is still offered with its note.

### 6.3 Multi-agent crew (Built, tested and run live)
- Storm desk is now three agents with separate instructions: a forecaster drafts the plan, a risk checker challenges each proposed move with a fact tool (what the source keeps, whether the receiver still runs low), and a summary writer produces the planner's plan.
- Guards: the risk checker may only check moves the draft named; the summary may only name moves the draft named; any sentence that names another move is dropped.
- The page shows "How the crew reached this plan", one turn per agent.
- Code: `backend/app/agent.py`. Tests: 13 agent and API tests.

- Live check: a real pending move (Jacksonville to Orlando, submersible pumps) was rejected with "No truck free". After the daily run, the learned route `S04 to S01 / pumps` had penalty 2.0 and last reason "truck unavailable", and the new pending move for Orlando's pumps came from Miami instead of Jacksonville.
- Bug found in this check and fixed: rejections were aged from the stock date, so a decision made today was dropped. Ages are now measured from the run time, with a regression test.
- The test rejection was undone afterwards: the move is pending again, and the test feedback and audit rows were removed.

### 6.4 Notes
- Live checks run: the simulator against the live endpoint and the time-travel history; the full build job (all tasks green, including the new learning step and the cost view); the feedback loop end to end.
- Crew verified live: three agents, 51 seconds, every cited transfer came from the tools. Risk checks used real stock figures (for example, Houston keeps 194 coolers after a 38-cooler move).
- Pending decision for you: a move (TR-AA073FE2E5, Tampa-bound 1000W generators) is APPROVED by your account at 05:29 UTC without a note. It was not one of my test actions, so I did not change it.

---

## 7. Still not done

- The Databricks App deployment (blocked by the company filter, as before).
- Lakehouse Monitoring for the feedback loop: the learning effect is shown only through the route notes, not a monitoring dashboard.
- The what-if dashboard tile.

---

## 8. MCP server and demo client (new folder `stormsense-mcp/`)

- **What:** the StormSense API exposed as ten MCP tools over Streamable HTTP (port 8200). Any MCP-capable assistant or app can read the plan, ask questions, run a what-if, and approve or reject transfers. The tools call the API, so its roles, rate limits and audit trail still apply.
- **Files:** `server.py` (tools), `demo_client.py` (dependency-free client: handshake, tool discovery, reads, optional agent and approve steps), `test_server.py` (six checks against a stand-in API), `README.md`, `pyproject.toml`.
- **Verified:** 6 of 6 tests pass. The demo ran end to end against a sample-mode API: discovery lists 10 tools, reads return data, approve changed one transfer, and the what-if and storm desk report that they need the live workspace in sample mode.
- **Live-data check (read path only):** the what-if returned live figures through the MCP server (Florida, strength 80: about 516 extra units, about $15.6k lost without moved stock).
- **Incident (undone, no data changed):** while testing, the demo's approve step reached the running live-mode API on port 8000 instead of a sample API, because port 8000 was already taken. The API refused it (403: that account is not a planner), and the transfer TR-05F77B4BDC is still pending. Afterwards I tested only against a sample-mode API on port 8001.
- **Not done:** the MCP server has not been deployed. It needs the same sign-in proxy as the app (see its README); the CareLoop folder `mcp/` was left unchanged.

- **MCP client agent (`stormsense-mcp/mcp_agent.py`):** a client that calls the MCP tools itself. A workspace chat model picks the tools; each check prints as it runs. Read-only unless `ALLOW_WRITES=1`. Verified on a sample API: it discovered the tools, ran three checks, and gave a plain answer citing transfer ids that came from the tools.
- **Model access without a separate key:** Gemini runs as a workspace serving endpoint (`databricks-gemini-3-5-flash`), so the CLI sign-in is enough. The CareLoop `mcp/.env` key is a Google AI Studio key; it is not used here.
- **Environment note:** the MCP folder must run on Python 3.12. On 3.13 the Databricks SDK call hung in this environment; the folder is pinned to SDK 0.149.0, the version the backend runs.

---

## 9. Documentation website (MkDocs Material)

- **What:** the docs in `docs/` are now a site built with MkDocs Material. It has search, dark mode, a planner guide, a five-minute demo, an MCP integration page and a generated API reference.
- **Files:** `mkdocs.yml`, `docs-requirements.txt` (pinned `mkdocs-material==9.6.14`), `docs/index.md` (home), `docs/planner-guide.md`, `docs/integrations/mcp.md`, `docs/api-reference.md` (generated), `docs/assets/logo.svg`, `infra/build_api_reference.py`.
- **Renamed:** `docs/architecture.md` is now `docs/system-design.md`. The old name collided with the architecture diagrams at `/architecture/` on the combined Pages site. Links updated in `README.md`, `contect.md` and the hub page.
- **Not published:** `what-changed.md` is not in the site because it contains an internal approval note. The architecture folder is excluded from the MkDocs build because it is built separately.
- **Build:** `make docs-site` builds into `site-build/` in strict mode, so a broken link fails the build. `make docs-serve` previews it at http://127.0.0.1:8001.
- **Checks:** strict build passes with no warnings; the home, planner guide and API reference pages load with no browser errors.
- **CI and hosting:** CI regenerates the API reference and fails if it differs from the committed file, then builds the site. The Pages workflow builds the site into `/docs/` beside the marketing page and the architecture diagrams. Live URL: `https://workatustadarshajay.github.io/STORMSENSE/docs/`.
- **Not done:** not committed or pushed. The Pages workflow publishes on the next push to `main`, so that push needs your go-ahead.

---

## 10. Carbon-aware transfers (novelty idea 14)

- **What:** every transfer shows an estimated carbon figure ("about 22 kg CO₂") next to its distance. Planners can see the environmental cost of a move as well as its money and time.
- **How it is estimated:** `backend/app/carbon.py`. A loaded medium-duty truck emits about 0.9 kg CO2e per mile, and a full truck carries about 200 units. A move's estimate is miles × 0.9 × (units ÷ 200). These are planning assumptions, labelled in the card's tooltip and the planner guide, not measurements.
- **What did not change:** the matching still chooses the nearest source. Carbon is shown, not used to change which moves are proposed. Approvals and stock are unaffected.
- **Files:** `backend/app/carbon.py`, `backend/app/service.py` and `backend/app/schemas.py` (new `co2_kg` field), `backend/tests/test_carbon.py` (new), `frontend/src/components/TransferCard.tsx`, regenerated `frontend/openapi.json`, `frontend/src/api/schema.d.ts` and `docs/api-reference.md`.
- **Test fixes found on the way:** `backend/tests/conftest.py` now pins the test identity. A local `backend/.env` had changed the default account, and `test_me_reflects_role` failed because of it. The browser tests' port is now set by `E2E_PORT` (default 8000), so they can run while another StormSense API is on 8000.
- **Checks:** backend 70 passed; web unit 36 passed; browser 27 passed (1 skipped, on port 8002); lint and type checks pass.
- **Not done:** using carbon to choose between sources, a carbon total on the overview, and carbon in the history page.

---

## 11. Hackathon deck updated (22 to 27 slides)

- **What:** `StormSense-Databricks-Hackathon.pptx` is rebuilt from the UST template with five new slides, and its figures are brought up to date. The template's sections and layouts are unchanged.
- **New slides:**
  - Decision tools: the what-if simulator and the storm desk crew.
  - Learning and carbon: the feedback loop and the carbon estimate.
  - Integrations: the MCP server, the built-in client agent, and the published sites.
  - Operations: data-quality gates, live weather in the daily job, and the cost view.
  - Roadmap: what is blocked, what needs a decision, and what comes next.
- **Figures updated:** 70 API and agent tests (14 of them for the storm desk crew), 18 library tests, 63 web tests (36 unit and 27 browser).
- **Checks:** `make deck` builds the file, and the verifier passes with 0 failures and 0 warnings, using real Arial metrics. No banned terms appear in the slides or the speaker notes.
- **Not checked:** the slides were not rendered to images, because LibreOffice is not installed here. The layout checks are geometric only.
- **Files:** `deck/build_deck.py` (slides, notes and titles), `deck/verify_deck.py` (slide count and order).
- **Speaker notes rewritten point by point (deck section 11 follow-up):** every slide's notes now lead with a short label (WHO, SAY, THE LIVE CHECK, IF ASKED ...), followed by the points to say, in order, with the figures checked against the running system. Stale counts were corrected: 70 API and agent tests, 63 web tests, 14 for the crew.
- **ROI slide corrected and filled (deck, business impact slide):** the slide now leads with the measured effect of live weather (shortages cut from 652 to 184 units, about 72%) and the current plan (11 moves, about $26.6k of sales protected, gross). Removed the earlier "$54k across 13 moves" and "nothing is estimated" wording, which no longer matched the live data. The speaker notes give the source of the 652 and 184 figures.

---

## 12. Prototype walkthrough in the deck (31 slides)

- **What:** four slides after the video show the running prototype, using fresh screenshots of the current app: the morning view, transfers (with the carbon figure), the what-if result, and Ask, History and the storm desk.
- **Source of the screenshots:** the dev web app connected to the live workspace, captured at 1280 by 800. The what-if was run once (read-only). No approval was clicked and the storm desk was not run, because a run calls the model. Files are in `deck/assets/shots/`.
- **Builder:** `deck/decklib.py` gained a picture helper with alt text, and `deck/build_deck.py` embeds each slide's images. The verifier expects 31 slides.
- **Checks:** the verifier passes with 0 failures and 0 warnings, using real Arial metrics. The pictures and notes were confirmed by reading the file back. Not rendered visually, since LibreOffice is not installed here.

---

## 13. Six features from the idea review (built and tested; live deployment waits for approval)

1. **Storm readiness per store (Built, tested, shown on Today).** Each store gets one percentage: the share of its products whose days of cover reach the storm window plus the safety days. Ready at 80% or more, Watch at 50% or more, otherwise At risk. Sample-data check: Orlando 20% (At risk, 2 storm days), Tampa 40%, most others 100%. Code: `backend/app/readiness.py`, `backend/app/service.py` (`stores()`), `frontend/src/pages/Today.tsx`.
2. **"Why not the closer store?" (Built, tested, takes effect after the next recommendations run).** A farther source now says in one line why the nearest store was passed over: it is also short, it has no spare stock, or a planner rejected that route recently. Sample data: 15 of 17 reasons now carry it. Code: `databricks/stormsense_core/planning.py` (`closer_store_note`). It changes reason text only; moves are unchanged.
3. **Export and print (Built, tested).** `GET /api/transfers/export` gives the plan as CSV, with spreadsheet formula characters neutralised in every cell. Transfers has a download link and a print button; "save as PDF" uses the browser's print dialog, so no PDF library is needed.
4. **Storm trigger from NWS warnings (Built and validated; not deployed, job paused).** `databricks/stormsense_core/alerts.py` reads active warnings for Florida, Texas and California, marks the plan-changing ones, and starts the daily cycle once for each new one. Notebook `13_storm_trigger.py`, table `alerts_seen`, job `stormsense_storm_trigger` every 15 minutes, paused by default (`trigger_status` variable). The bundle validates. It has not run against the live NWS feed.
5. **Backtest of past storms (Built, tested, shown at /backtest; linked from History).** `databricks/stormsense_core/backtest.py` replays each named storm with what really sold. Sample result: lost sales were about $171k for Hurricane Marlow, and nearby stock could have covered only about 2% of it. Across the five sample storms, the share protected ranges from 0% to 29%. This is an honest finding about the sample data, not a figure to present as a result: nearby stores had little spare stock at the start of these storms. Notebook `14_backtest.py` and table `backtest_results` are in the build job.
6. **Planner notes feed the risk checker (Built, tested; SQL lookup, not Vector Search).** The risk checker can call `get_precedents` for a draft move and quote the last decision on the same route and product, with its reason. It is limited to transfers in the draft, as before. This uses a plain database lookup, not Vector Search: Vector Search needs a billable endpoint, and the embedding models (`databricks-gte-large-en` and others) are present in the workspace. Adding it is a deployment decision for later.

**Checks:** backend 76 tests pass; databricks library 24 pass; web unit 40 pass; browser 27 pass with 1 skipped; lint passes; `databricks bundle validate` passes; the docs site builds in strict mode.

**Not done yet, and needs your approval:**
- Deploy the bundle, so the backtest and the trigger job exist in the workspace. The trigger stays paused until you unpause it.
- Run the recommendations job once, so the "closer store" lines appear on live transfers. This changes only reason text; approved and rejected rows are never touched.
- Create the Vector Search endpoint if you want semantic search instead of the SQL lookup.
- The hosted app is still blocked by the company network filter, so these features are visible locally only.

---

## 14. Weather switch: live or demo storm (app display)

- **Live weather (default):** the real forecast. Nothing changes for existing users; every response says `weather_source: "live"`.
- **Demo storm:** on Today, a switch sets `?weather=demo`. A storm is placed on the Florida stores for the next two forecast days, which changes the alerts, the storm readiness, and the store forecast weather. Each response says `weather_source: "demo"`, and Today shows a banner: stock figures and transfers still come from the live plan.
- **Why transfers don't change:** the stock plan is built by the daily job from the weather table. Changing the display alone keeps approvals and the audit trail true to real data.
- **Job-level switch (unchanged):** the bundle variable `weather_provider` (`nws` or `sample`) decides what the daily job uses. Changing it changes the plan the next time the job runs.
- **Code:** `backend/app/demo_weather.py`; `service.py` (`_weather`, mode-aware overview, stores and forecast); `api.py` (`weather` query parameter on `/api/overview`, `/api/stores`, `/api/stores/{id}/forecast`); `frontend/src/pages/Today.tsx` (switch and banner).
- **Checks:** backend 80 pass, web unit 41 pass, browser 27 pass with 1 skipped; lint passes.

---

## 15. Price markdown suggestions (revenue from surplus stock)

- **What:** for surplus stock that would not sell at full price within 14 days, the app suggests the smallest discount (10% to 40%) that clears it and brings in more cash than holding it. Shown on Today under "Price markdowns" with the cash it adds.
- **Rule and assumptions:** `backend/app/markdown.py`. Each 10% off lifts sales by 15% (an assumption to test on a pilot). Discounts stop at 40% because there is no cost data yet. No suggestion is made when a discount would lose money.
- **Read-only:** suggestions only. No price changes are written anywhere.
- **Sample result:** one suggestion, Los Angeles 1000W generators, 10% off, about $260 more than holding the stock. The rule is conservative on purpose: most sample surplus either sells at full price in time or is too large for a discount to pay.
- **Code:** `backend/app/markdown.py`, `service.py` (`markdowns()`), `GET /api/markdowns`, `frontend/src/pages/Today.tsx`. Docs: planner guide.
- **Checks:** backend 85 pass (4 rule tests and an endpoint test); web unit 42 pass; browser 27 pass with 1 skipped; lint passes.
- **Not done:** cost and margin (needed to confirm a discount never sells below cost); pipeline table; the elasticity needs a pilot.
- **Demo markdowns (section 15 follow-up):** in demo weather, markdowns use a stronger response assumption (each 10% off lifts sales by 40%, against the live 15%), so the rule has examples to show. The page labels the assumption. Live results are unchanged: the live rule finds none on this week's data, because even 40% off cannot clear large surplus at a 15% response. Checks: backend 87 pass; web unit 43 pass.

---

## 16. Job emails to a configurable address (configured, not deployed)

- **What:** the build job and the daily job send failure emails to the deploying account and to `alert_email`. The daily job also sends a "plan ready" email on success, which covers each morning's run and each storm-triggered refresh. The storm trigger sends failure emails only, because a success email every 15 minutes would flood the inbox.
- **Where the address lives:** the bundle variable `alert_email`, given at deploy time, so it is not written into the repository. The validated configuration showed the recipients for each job.
- **Not yet sent:** nothing is deployed. Deploying is what makes these emails start. Until then the jobs send nothing new.
- **Known limits:** job emails use Databricks' own wording (for example, "job succeeded"), not a custom message. A blank `alert_email` adds an empty recipient, which the Jobs API may reject, so always pass the address. Whether external addresses such as Gmail are allowed by the workspace must be checked on the first test.
- **Deploy command (after your approval):** `cd databricks && databricks bundle deploy --profile stormsense --var alert_email=<address>`

---

## 17. Demo storm email button

- **What:** on Today, in demo weather, **Email this storm alert** sends one message to the demo address: the storm, the urgent and waiting counts, a link to Transfers, and a reminder that planners approve each move.
- **Who:** planners only. Limited to three sends a minute. Off until the mail settings are configured; when they are not, the button says so.
- **Secrets and addresses:** the mail password is a `SecretStr` in the environment. The address and password never appear in responses, logs, or the code. `infra/.env.example` lists the settings.
- **Code:** `backend/app/alerts.py` (message and sending), `api.py` (`POST /api/demo/alert`), `config.py` (settings), `frontend/src/pages/Today.tsx` (button).
- **Not sent yet:** nothing has been sent. The first send needs the mail settings, and a test with your address.
- **Checks:** backend 92 tests (5 new); web unit 44 (1 new).

---

## 18. Databricks SQL alert for urgent moves (script ready, not created)

- **What:** `databricks/scripts/create_storm_alert.py` defines a Databricks SQL alert, "StormSense - Urgent moves waiting". It checks every hour and emails the address when urgent moves are pending. It sends nothing on "all clear", and at most once an hour while urgent moves remain.
- **Why no mail password:** Databricks sends the email, so there are no credentials to store.
- **Dry run:** the script prints the definition and changes nothing. The check that `--apply` would create uses the same definition shown in the dry run.
- **Before applying:** the live data has one urgent pending move, so the alert would email within the first hour. Confirm the address and the warehouse first.
- **Not done:** the alert is not created. The email button on Today still uses the SMTP settings, which are not configured. The alert is driven by the data, not by the button; if you want the button, the job-run route is still needed.

---

## 19. Demo email button now uses a Databricks job (no mail credentials)

- **What:** **Email this storm alert** starts the job `StormSense - Demo storm alert`. Databricks emails the alert address when the job succeeds. The SMTP sender and its settings are removed, so no mail password is needed or stored.
- **Who:** planners only, and at most three starts a minute. Sample data cannot start jobs, so the button says so there.
- **Job:** `databricks/resources/jobs.yml` (`stormsense_demo_alert`) runs `notebooks/15_demo_alert.py`, which only finishes. It has no schedule, so it costs nothing until clicked. The bundle validates.
- **Before the button works:** deploy the bundle with the alert address (`--var alert_email=...`). Until then the button says the job isn't in the workspace yet.
- **For the deployed app:** its identity needs permission to run this job. That is set when the app is deployed.
- **Checks:** backend 93 pass (5 for the button); web unit 44 pass.

---

## 20. Interconnectability page in the docs

- **What:** `docs/integrations/interconnect.md`, under Integrations. It explains the three ways another system can use StormSense: an AI assistant through the MCP server (nothing to build), the REST API (for your own screens), or the full web app. It includes a decision guide, the MCP tool list, curl examples, the header and identity rules, and a security checklist.
- **Accuracy:** the tool list and endpoints match the code. Writes need `X-Requested-With: stormsense`; identity comes from `X-Forwarded-Email`, which only the sign-in proxy sets in deployment.
- **Status stated on the page:** the MCP server and API run locally, and the hosted deployment is still blocked.
- **Also updated:** the home page's "Building on it" row links to the new page. The docs site builds in strict mode.
