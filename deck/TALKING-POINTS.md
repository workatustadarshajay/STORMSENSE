# StormSense — talking points

What to say for each of the ten content slides in `StormSense-overview.pptx`
(slides 2–11). The intro (slide 1) and thanks (slide 12) frame the deck; the
substance is below.

Each slide gets four things: **the concept** (what the slide is really arguing),
**say this** (the spoken version), **the numbers** (what to cite, all measured
outputs of the running system on generated sample data), and **the bridge** (the
sentence that carries you to the next slide).

> One thing to state up front, because it frames the whole deck: our problem
> statement is **not** the ideathon brief. The brief was the context we were
> given. Our problem statement is the specific one on slides 2–4 — weather moves
> demand faster than inventory moves, and the planner has no way to act in time.

---

## Slide 2 — Problem · "Weather moves demand faster than inventory moves"

**The concept.** Weather is the demand signal the business already has, but it is
not connected to store-level stock. Demand for weather-sensitive goods moves in
days; inventory moves in weeks. That gap, not the weather itself, is the problem.

**Say this.** "A named storm in the forecast pulls generators, tarps, pumps and
plywood forward within days — and only in the stores in its path, not chain-wide.
Heat does the same for coolers and pumps. Two different drivers can hit two
different regions in the same week. And because weather is hyper-local, a
shortage and a surplus can sit one region apart while both are true at once."

**The numbers.** 10 stores across Florida, Texas and California. 5
weather-sensitive products. 12 months of daily history. A 7-day horizon.

**The bridge.** "So the two problems — running out, and holding too much — are
not sequential. They happen on the same morning."

---

## Slide 3 — Problem · "Shortages and surplus happen at the same time"

**The concept.** This slide is the evidence that the problem is real and
measurable, not hypothetical. On the same day, the same network is simultaneously
short and overstocked.

**Say this.** "This is one day's snapshot: 50 store-by-product positions. Eleven
are short on a product the forecast says will sell, sixteen are holding more than
the week needs, and twenty-three are balanced. Because both exist at once, the
cheapest fix is not to buy more — it is to move what is already on the network."

**The numbers.** 50 positions → 23 balanced, 16 surplus, 11 shortage.

**The bridge.** "The fix is a store-to-store move. But someone has to make that
call, and that person is the constraint."

---

## Slide 4 — Problem · "Planners need a decision, not another dashboard"

**The concept.** The audience defines the deliverable. Three constraints —
non-technical, phone-first, time-boxed — rule out most analytics output and point
at a single thing: a ranked, plain-language recommendation.

**Say this.** "The people who act are merchandising and store planners. They
think in stores, products and weeks — not tables, queries or error metrics. They
work away from a desk. And the window is days, not a weekly meeting. So the
deliverable is not another chart. It is a ranked recommendation a planner can
approve in seconds."

**The numbers.** 7 days of forecast against a decision window of a few days.

**The bridge.** "That is the problem. Here is the product that solves it."

---

## Slide 5 — Solution · "One question, answered every morning at 6:00 AM"

**The concept.** One question, answered automatically, every morning: given the
weather this week, which stores run short, which have extra, and what should move
where. The whole pipeline exists to produce the last box — and the last box is
deliberately a human.

**Say this.** "A scheduled job runs at 6:00 AM Eastern and is idempotent —
running it twice does not change the answer. It refreshes weather, rebuilds
features, scores with the current champion model, finds the gaps, and writes
ranked transfer recommendations. The planner only ever sees the last box:
approve or reject. We never move stock without a person deciding."

**The numbers.** Five stages — weather → forecast → shortage/surplus → transfer →
planner decides. Daily, 6:00 AM Eastern.

**The bridge.** "It is one question for the planner, but it is three layers
underneath."

---

## Slide 6 — Solution · "Three layers, one decision"

**The concept.** Separation of concerns, with one hard rule: the browser never
talks to Databricks. Databricks owns the data and the forecast; the API owns the
rules, roles and audit; React owns the planner's experience.

**Say this.** "Databricks holds 15 Delta tables in Unity Catalog, builds
leak-free features over a 7-day horizon, and serves the champion model by alias.
The FastAPI gatekeeper is the only path to that data — bound-parameter SQL, roles,
guarded approvals, every attempt written to an audit trail. And the React app is
where the planner works: Today, Transfers, Store forecast, Ask. The browser never
sees Databricks, and the service principal never reaches the client."

**The numbers.** 15 tables. 3 layers. 5 planner screens.

**The bridge.** "Dividing it this way is what makes it safe. The next slide is
what makes it trustworthy."

---

## Slide 7 — Solution · "Built to be trusted, and safe to re-run"

**The concept.** Trust is the feature. A planner will only act on a
recommendation they believe, and will only keep acting on it if an approval is
obviously safe. Three guardrails deliver that.

**Say this.** "First, the model has to earn its place — it is promoted to champion
only if it beats 'same as last week' and the trailing 28-day average on held-out
data. Second, an approval cannot double-apply: only still-pending rows change,
stamped with a request id, so a repeat or a second person is told it is already
handled. Third, re-running changes nothing it should not — forecast, gaps and
weather replace a single day, and recommendations merge into pending rows only.
No decided row is ever overwritten."

**The numbers.** 2 baselines to beat. 1 idempotent approval path. 0 decided rows
overwritten.

**The bridge.** "That is the design. Now the measured result."

---

## Slide 8 — ROI · "The forecast beats the naive baselines"

**The concept.** Accuracy is the whole value proposition, so it is measured
against the baselines the business effectively runs on today — not against
nothing. Lower weighted error means fewer wrong calls about where stock should go.

**Say this.** "The champion model's weighted forecast error is 0.40. 'Same as last
week' is 0.67, and the trailing 28-day average is 0.57. That is roughly a 40%
reduction against the baseline the business runs on today. It is measured on the
last 28 days, held out from training — a time split, never a random split."

**The numbers.** WAPE 0.403 champion vs 0.667 and 0.571. ~40% lower error than
"same as last week".

**Say honestly.** These are measured outputs of the running system on generated
sample data — not production numbers. The mechanism and its measured accuracy are
real; the absolute figures scale with real feeds.

**The bridge.** "That is per-forecast accuracy. Here is what it means at the
scale of a planner's morning."

---

## Slide 9 — ROI · "Decisions in minutes, not days"

**The concept.** The return is not only accuracy — it is the collapse of a manual,
reactive review into a short ranked list, so the planner's time goes into deciding
rather than assembling.

**Say this.** "Each run produces 350 forecasts — 10 stores by 5 products by 7
days — and classifies 50 stock positions. Of those, 13 carry a transfer
recommendation, 4 are urgent, and together the moves cover roughly 54 thousand
dollars of sales at risk. Work that used to be a manual review now arrives as a
short list waiting for a decision."

**The numbers.** 350 forecasts · 50 positions · 13 recommendations · 4 urgent ·
~$54k of sales covered.

**Say honestly.** Snapshot of one daily run, on generated sample data.

**The bridge.** "That is the outcome. Briefly, what it is built on."

---

## Slide 10 — Technologies · "Databricks: the data and forecasting engine"

**The concept.** This is where the idea meets the platform the organisation
already runs. Every capability used is one the business already has, plus the
model itself.

**Say this.** "Unity Catalog holds 15 Delta tables as the single governed home for
stores, products and forecasts. Ten serverless notebooks build the pipeline — no
clusters to size. MLflow and the Model Registry version the model, and the live
model is served by alias, so promotion is a one-line change. Workflows runs the
6:00 AM cycle with retries and failure email. Genie gives a read-only space for
open questions — it answered all ten sample questions correctly and cannot change
data. And everything — tables, jobs, model, app — is created from code via
Declarative Automation Bundles, with RBAC and Unity Catalog grants for least
privilege. The model is scikit-learn's HistGradientBoosting with Poisson loss,
which runs on serverless without a custom cluster."

**The numbers.** 15 tables · 10 notebooks · 1 daily job · 10/10 Genie answers.

**The bridge.** "That is the engine. The last piece is what the planner touches."

---

## Slide 11 — Technologies · "Application stack"

**The concept.** The application stack is deliberately boring and well-tested,
because the differentiator is the forecast, not the framework.

**Say this.** "FastAPI and Python 3.12 behind a React 18 and TypeScript app, built
with Vite and Tailwind 4, with React Router and TanStack Query keeping the
screens responsive and honest about loading, empty and error states. SQL is always
bound-parameter — never string-built. Quality is part of the stack: pytest for the
library and API, Playwright for real browser journeys, plus accessibility and
console-error checks in CI. Everything runs on sample data with one command and
against the real workspace after configuration, so it is demonstrable anywhere."

**The numbers.** 63 Python tests · 25 web unit tests · 23 browser tests.

**The bridge.** "And that is StormSense — weather in, a ranked inventory plan
out, and a decision in minutes."

---

## If you are asked

**"Is this real data?"** No — the dataset is generated sample data, and the UI and
this deck label it as such. The pipeline, the model and every number quoted are
real outputs of the running system.

**"How accurate is it, really?"** Weighted error 0.403 on a held-out 28-day window,
against 0.667 and 0.571 for the two baselines. It is a time split, so no future
information leaks into training.

**"What if the model is wrong?"** That is why the last step is a person. Nothing
moves without an explicit approval, and every attempt — approved, rejected or
skipped — is written to an audit trail.

**"How much did it cost to run?"** The pipeline is serverless and scheduled, so it
costs only the minutes it runs. It can be paused with one command.

**"Is it deployed?"** The data, forecasts and daily job run in the workspace. The
app has been run locally against the real workspace, including real approvals; the
hosted app deployment is a separate, known step.

**"What is next?"** Connect real sales, stock and weather feeds; host the app on
the workspace with sign-in and roles; then widen the product and store set.
