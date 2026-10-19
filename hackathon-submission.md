# Hackathon submission: StormSense

Copy each section into the matching form field.

---

## Title

StormSense: move stock before the storm, not after

---

## Description

Weather moves demand in days, but stock moves in weeks. A storm can empty the shelves of generators, tarps, pumps and plywood in the stores in its path while a store one region away holds more than it needs. Planners see the problem too late, and they have no simple way to act on it.

StormSense connects the weather to store-level stock. Each morning it forecasts seven days of demand for every store and product, finds the stores that will run short and the nearby stores with spare stock, and proposes store-to-store transfers. A planner reviews each move with its reason, the sales it protects and how confident the forecast is, then approves or rejects it. Every decision is recorded.

It runs on Databricks: Unity Catalog holds the data, a forecaster is registered with the `champion` alias and is promoted only if it beats two simple baselines, and a daily job runs at 6:00 AM Eastern. The planner app is a single process with its own service principal, so the browser never sees a table, a query or a credential.

All data in the demonstration is synthetic sample data, except the public National Weather Service forecast used by the daily job. In the sample history, five past storms and heat events lost about $302,000 of sales. On the sample plan, the moves protect about $50,000 of revenue. That protected figure is an upper bound.

---

## Alignment with criteria levers

**Alignment to Databricks features (30%).** Unity Catalog governs the data and the registered forecaster. MLflow tracks the forecaster, and Model Serving scores it for the daily run and the what-if simulator. Genie powers the read-only Ask space. A Lakeflow pipeline runs data-quality checks, and Jobs run the daily 6:00 AM cycle and an optional storm trigger. Every screen reads through a serverless SQL warehouse. The app is defined as a Databricks App but is not deployed yet.

**Novelty (30%).** A weather-led forecast at store and product level, with features built only from what was known on the day. A planner-first design: the system proposes, and nothing moves without approval. A read-only storm desk in which three agents draft a plan and a risk step checks each move. A what-if simulator that compares a normal week with a storm week using the same forecaster. A feedback loop, in which rejection reasons adjust route rankings for the next run without adding or removing moves.

**Demo (10%).** A five-minute scripted demo on sample data (`make dev-sample`), with the same screens on the workspace after the daily run.

**Business impact (20%).** See the business outcomes section below.

**Presentation and Q&A (10%).** A 20-slide deck with a five-minute speech and speaker notes, and a risks slide that names the limits before anyone asks.

---

## Solution requirements

Each requirement from the brief, and how StormSense meets it.

**1. A well-defined business problem.** Met. Home improvement stores run out of weather-sensitive products (generators, tarps, pumps, plywood, coolers) in the stores in a storm's path while nearby stores hold spare stock. The planner has no simple, timely way to move that stock. The problem is stated in the description and on slide 3 of the deck.

**2. A practical Databricks-enabled approach.** Met. The data sits in Unity Catalog. A daily job runs on serverless compute. The forecaster is trained, tracked in MLflow and served from a model endpoint. Each screen reads through a serverless SQL warehouse.

**3. Clearly articulated business outcomes.** Met, on sample data, and labelled as such. Revenue: about $50,000 of protected sales on the sample plan. Cost: about $2,000 saved across seven truck routes by sharing trucks. Risk reduction: stores that would run short are flagged before the storm. See the business outcomes section below.

**4. Original work by the team.** Met. The application, the data generators, the forecasting code and the interface were written for this project. The landing page's layout took inspiration from a reference design the team was shown, but its code, copy and visuals are original. No third-party video or code is used.

**5. No infringement of intellectual property, privacy, security or compliance requirements.** Met. The app uses sign-in with workspace accounts and roles. It runs as its own service principal, uses fixed, parameterised SQL and records every decision in an audit trail. It has no personal access tokens and no secrets in code. Automated tests check the SQL rules and the banned-words rule.

**6. Scalable, practical and feasible for enterprise adoption.** Partly met. It runs on managed Databricks services (Unity Catalog, Jobs, Model Serving, a SQL warehouse), so it needs no extra infrastructure. The demonstration covers 10 stores and 5 products. Growing to thousands of stores would mean moving the driver-side pandas logic to Spark, which is noted as a known limit.

**7. A working prototype, proof of concept, simulation or visual demonstration.** Met. The planner app runs end to end on sample data with one command (`make dev-sample`), and the same screens run against the workspace. There is a five-minute scripted demo, a what-if storm simulator, and an automated test suite (172 backend and data tests, 57 frontend tests).

**8. Data is non-confidential, synthetic, public or approved.** Met. The sample sales, stock and store data is generated. The weather forecast in the daily job comes from the public National Weather Service. Names of people in the demo are invented.

**9. Clearly articulated business outcomes across categories.** Met. See the business outcomes section below. Revenue, cost, risk and efficiency are each covered. Customer experience and productivity are described, but not measured yet.

**10. Meaningful use of Databricks capabilities.** Met. Lakehouse and Unity Catalog (Delta tables, governed in the catalog). Data Engineering (Jobs, a Lakeflow data-quality pipeline). AI/ML (a forecaster tracked in MLflow, served from a model endpoint, promoted only if it beats two baselines). GenAI (a read-only storm desk that drafts a plan with a serving-endpoint chat model, checked by a risk step). Genie (the Ask space). Analytics (a Lakeview overview dashboard, deployed and not yet visually checked). Agent Bricks is not used.

**11. A relevant home improvement retail problem.** Met. The products (generators, tarps, pumps, plywood, coolers) and the stores (home improvement planners) are the core of the problem.

---

## Business outcomes

| Category | Outcome | Evidence (sample data) |
|---|---|---|
| Revenue | Sales protected by moving stock before a storm | About $50,180 of protected sales on the sample plan. An upper bound. |
| Cost optimisation | Fewer truck trips by sharing trucks on a route | About $2,000 saved across seven routes; 14 trips become 9. |
| Risk reduction | Stores that would run short are flagged before the storm | Five stores at risk on the sample plan. |
| Operational efficiency | One screen shows the moves, their reasons and their confidence; the planner decides in one place | Not measured yet. |
| Customer experience | Fewer empty shelves during a storm | Not measured yet. Expected, not claimed. |
| Productivity | Replaces manual, late stock checks with a daily plan | Not measured yet. |

**Net on the sample plan:** about $8,600, after a 30% margin on protected sales and trucking costs. The margin is an assumption, and a store can set its own.

**Limits we state openly:** the protected figure is an upper bound from a backtest that uses what really sold. The forecast has an error of about 0.4 on sample data. The app is defined as a Databricks App but is not deployed yet, and real sales, stock and weather feeds are not connected yet.
