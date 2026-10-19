# What StormSense is, in plain words

**StormSense is a planning tool for store planners.** Each morning it looks at the weather coming for each store, forecasts how much of each product will sell, and finds where stock will run out and where it is sitting unused. Then it proposes what to do about it. A planner reviews every proposal and decides.

## What it does, and what it does not

| It does | It does not |
|---|---|
| **Proposes moves** of stock that is already in the network: from a store with spare stock to a store that will run short, with the reason and the sales it protects. | **Buy anything.** It has no purchase orders, no supplier ordering, and no suggestion of what to buy. |
| **Suggests markdowns** on surplus that would not sell at full price in time (10% to 40% off), with the cash it would bring in. | **Move or sell anything by itself.** Every move and markdown waits for a planner's approval. |
| **Drafts a storm response:** the moves, the markdowns, the impact, and a short note for each affected store. The planner approves some and rejects the rest in one step. | **Guarantee sales.** It estimates what can be protected, and the estimate depends on the stock that exists. |
| **Answers questions** in plain language (Ask), and runs "what if a storm comes" scenarios without changing anything. | **Use real sales or weather feeds yet.** Today it runs on generated sample data, plus the public National Weather Service forecast. |

## What happens when a storm is coming (example)

| When | What the app does | What the planner does |
|---|---|---|
| **Days before** | The daily run forecasts seven days per store and product. Shortages and surpluses are found. | Opens Today: sees the urgent moves, the stores running low and the next alert. |
| **Storm plan** | The storm response page drafts the plan: the stock moves that protect the most sales, the markdowns on surplus, and a note for each store. | Reads each move's reason and confidence. Approves the ones to go ahead, rejects the rest. |
| **After the decision** | Approved moves are recorded and counted as stock arriving or leaving, so the gap view updates. Every decision is audited. | Checks History for who decided what. Rejections teach the route ranking for the next run. |
| **After the storm** | The impact page shows the sales protected and the net after margin and trucking. | Reviews the result, and decides what to change. |

## Your questions, answered directly

- **"When a storm comes, will we protect them?"** It helps protect sales by moving stock to the stores that will run out, before the storm arrives. It cannot protect sales that have no stock to move. On sample data, the backtest protects about 4% of past lost sales as an upper bound.
- **"Which products should we sell?"** It suggests markdowns on surplus stock that is unlikely to sell at full price in time. It does not choose what to sell in general.
- **"Which products should we buy?"** The app does not tell you what to buy. Buying is a planned idea for later, not something it does today.
- **"Does it act on its own?"** No. The system proposes; a planner approves or rejects. The only automatic part is the morning forecast and the proposals it makes.

**Honest limits:** the storm plan and its drafts are kept in memory, so they reset when the server restarts. The storm desk and the what-if simulator need the live workspace. Everything else runs on sample data unless the workspace is connected.

---

# StormSense: 7-minute script

**Presenter:** Adarsh Ajay
**Total time:** 7:00 = **4:00 presentation** (slides) + **3:00 live demo**
**Slides:** `stormsense_presentation.pptx` (20 slides). Slides marked SKIP are not presented aloud. Keep them in the file as backup.

The scripts are sized for 150 words a minute, which is about 2.5 words a second. Each script's word count is in brackets, so you can check it against the time. If you run long, cut the "Remember" bullets first, not the spoken lines.

---

## Clock at a glance

| Slide | Title | Start | Length | Ends |
|---|---|---|---|---|
| 1 | Title | 0:00 | 0:15 | 0:15 |
| 2 | Agenda | | SKIP | |
| 3 | Why storms hurt profit | 0:15 | 0:30 | 0:45 |
| 4 | The idea in three steps | 0:45 | 0:20 | 1:05 |
| 5 | Four parts, one daily loop | | SKIP | |
| 6 | The app at a glance | 1:05 | 0:15 | 1:20 |
| 7 | High-level architecture | 1:20 | 0:15 | 1:35 |
| 8 | The daily job | | SKIP | |
| 9 | Security and safety | 1:35 | 0:10 | 1:45 |
| 10 | Lost sales in past storms (chart) | 1:45 | 0:25 | 2:10 |
| 11 | Past storms: the numbers | | SKIP | |
| 12 | What the current plan is worth | 2:10 | 0:20 | 2:30 |
| 13 | Options compared | 2:30 | 0:10 | 2:40 |
| 14 | Options 1 and 2 | 2:40 | 0:15 | 2:55 |
| 15 | Option 3, and how to test | 2:55 | 0:15 | 3:10 |
| 16 | Demo flow (bridge to live demo) | 3:10 | 0:05 | 3:15 |
| 17 | Test results | 3:15 | 0:10 | 3:25 |
| 18 | More ideas to grow profit | 3:25 | 0:10 | 3:35 |
| 19 | Risks and limits | 3:35 | 0:15 | 3:50 |
| 20 | Thank you | 3:50 | 0:10 | **4:00** |
| | **Live demo** | 4:00 | 3:00 | **7:00** |

**Check against the clock:** if you are more than 15 seconds behind at slide 10, skip slide 13 and say its one point during slide 14.

---

## Slide 1: Title (0:15)

**Show:** the title slide.

**Say:** [38 words]
"Good morning. I'm Adarsh Ajay. This is StormSense, which moves stock before the storm, not after. In four minutes I'll show you the problem, how it works, and what it's worth. Then I'll show it live."

**Remember:**
- Look at the audience, not the screen.
- Skip the agenda. This sentence gives the order.

---

## Slide 2: Agenda: SKIP

---

## Slide 3: Why storms hurt profit (0:30)

**Show:** the manual-process table, with the $302,000 caption.

**Say:** [75 words]
"Picture a store on a Thursday. A storm is due Sunday. The generators are in Tampa, and Orlando is about to run out. Today, someone reads a spreadsheet after the warning and phones a neighbour. In our sample history, five past storms and heat events lost about 302,000 dollars of sales. The gap is not the weather. The stock is in the wrong place, and nobody knows in time."

**Remember:**
- Say "sample history" the first time you give the $302,000.
- End on "the wrong place". The next slide starts from there.

---

## Slide 4: The idea in three steps (0:20)

**Show:** Predict, Move, Decide.

**Say:** [55 words]
"StormSense works in three steps. It predicts demand for every store and product, seven days ahead. It moves stock, proposing transfers from stores with spare stock to stores that will run short. And the planner decides, approving or rejecting each move. The system does the arithmetic. The planner stays in control."

**Remember:**
- Pause after each step word. The audience should be able to repeat them.
- This is the most important slide. Protect its time.

---

## Slide 5: Four parts, one daily loop: SKIP

---

## Slide 6: The app at a glance (0:15)

**Show:** the Today, Transfers and History screens.

**Say:** [37 words]
"This is what a planner sees. Today shows the urgent moves and the next weather alert. Transfers shows each move as a sentence, with its reason. The label says sample data, and it stays on."

**Remember:**
- Point at the "Sample data" label once.
- Describe what the planner does on each screen. Don't read the screens.

---

## Slide 7: High-level architecture (0:15)

**Show:** the architecture diagram.

**Say:** [37 words]
"This is the whole application. The forecast runs on Databricks each morning. The app is one process, and it is the only part that talks to the workspace, so the browser never sees a table or a password."

**Remember:**
- Name two boxes only: the Databricks workspace and the single app process.
- Say "managed services" once if you have a second.

---

## Slide 8: The daily job: SKIP

---

## Slide 9: Security and safety (0:10)

**Show:** the security bullets.

**Say:** [25 words]
"For enterprise use, people sign in with their workspace account. Roles decide who can approve, and every decision is audited."

**Remember:**
- This answers "is it safe" before anyone asks. Say it in one breath.

---

## Slide 10: Lost sales in past storms (0:25)

**Show:** the column chart.

**Say:** [64 words]
"Each pair of bars is one storm: the sales we lost, and what the planned moves could protect. The protected bar is an upper bound, because it uses what really sold. Even so, the gap is large. We protect about four percent today. Heat events protect the most, about twenty-eight percent, so that is where to start."

**Remember:**
- Point at the largest pair first: Hurricane Marlow, about $171,000 lost in sample history.
- Say "upper bound" out loud. It earns trust for the rest of the talk.

---

## Slide 11: Past storms: the numbers: SKIP

---

## Slide 12: What the current plan is worth (0:20)

**Show:** the five figure tiles.

**Say:** [50 words]
"On the sample plan, the proposed moves protect about 50,000 dollars of revenue. After a 30 percent margin and trucking, the net is about 8,600 dollars. Net is the number that matters, not revenue. The assumptions are in the footnote."

**Remember:**
- Say "net" every time you give 8,600. Never let revenue be quoted as profit.

---

## Slide 13: Options compared (0:10)

**Show:** the options table.

**Say:** [25 words]
"There are six options. Two can start this quarter with what we already have. The others need a pilot or more modelling."

**Remember:**
- Don't read the table. Move on.

---

## Slide 14: Options 1 and 2 (0:15)

**Show:** the truck loads and markdowns slide.

**Say:** [37 words]
"Option one: share trucks on a route. Fourteen trips become nine, saving about 2,000 dollars. Option two: markdowns on slow stock, an estimated 260 dollars more on one example. That lift is an assumption, so we pilot it first."

**Remember:**
- Lead with the truck saving. It is the firmest number here.
- Say "estimated" for the markdown.

---

## Slide 15: Option 3, and how to test (0:15)

**Show:** the warning trigger and pilot steps.

**Say:** [37 words]
"Option three: start moves on a weather warning, not the forecast alone. It is built and paused, and not measured yet. To test any option, run a pilot against control stores, and widen only if it beats the control."

**Remember:**
- Say "not measured yet" plainly.
- End on "beats the control". That is the measurement.

---

## Slide 16: Demo flow: bridge to live demo (0:05)

**Show:** the demo flow.

**Say:** [12 words]
"Now the live demo, on sample data."

**Remember:**
- Have the app open on /today before you start, and switch to it now.

---

## Slide 17: Test results (0:10)

**Show:** the test results.

**Say:** [28 words]
"172 backend and data tests pass, and 57 frontend tests. On sample data, the forecast's error is about 0.4, against 0.67 and 0.57 for the baselines."

**Remember:**
- Say "sample data" before the forecast figures.

---

## Slide 18: More ideas to grow profit (0:10)

**Show:** the ideas list.

**Say:** [18 words]
"Ideas not built yet. First, heat planning, because heat events protect the most. Second, regional pre-storm buying."

**Remember:**
- Name only the top two.

---

## Slide 19: Risks and limits (0:15)

**Show:** the risks list.

**Say:** [32 words]
"Our limits, from me first. The data is sample data, and real feeds are not connected. Gross revenue is not profit. The backtest is an upper bound. The Databricks App is defined, not deployed."

**Remember:**
- State the limits. Don't apologise for them.

---

## Slide 20: Thank you (0:10)

**Show:** the thank-you slide.

**Say:** [18 words]
"Our ask: test one option, in one region, this season. Thank you. Let's see it working."

**Remember:**
- Switch to the browser on the last line.

---

# Live demo (3:00)

**Start:** the app is open on `/today` with the "Sample data" label visible.

| Time | Step | Do | Say |
|---|---|---|---|
| 4:00 | 1. Today (30s) | Show the urgent transfers, stores running low and the heat alert | "Seven urgent moves this morning, and five stores at risk." |
| 4:30 | 2. Transfers (50s) | Open Transfers, read one reason, approve the first two | "This move is 54 generators from Jacksonville to Orlando, because the storm is on Sunday. Approved. Two transfers approved." |
| 5:20 | 3. Stores and Ask (60s) | Open Stores, point to Orlando running low on Thursday. Open Ask and ask "Which stores will run out of generators this week?" | "Orlando runs low on Thursday, 53 units short. Ask answers in one sentence and cannot change anything." |
| 6:20 | 4. History and repeat approval (40s) | Open History. Try the same approval again | "Every decision is recorded with who and when. A repeat approval is refused: already handled by someone else." |
| 7:00 | End | Return to the slides for questions | "Happy to take questions." |

**Demo remember:**
- If a screen is slow, skip it and move on.
- If the app fails, use the screenshots from slide 6 and say what would happen.

---

## Words to avoid

- Don't say "guaranteed", "will save" or "will increase revenue". Say "estimated", "upper bound" or "on sample data".
- Don't say "PoC" or "prototype". Say "working app" or "running system".

---

## Final check before you start

1. Title: name and one line.
2. Thursday story: sample history.
3. Three steps: predict, move, decide.
4. Net, not revenue.
5. Upper bound, every time.
6. Limits before questions.
7. Demo: Today, Transfers, Stores and Ask, History.

**Presentation: 4:00. Demo: 3:00. Total: 7:00.**

---

# How we used Databricks

Use this as a reference for questions about the platform. It is not in the 7-minute timing. If a judge asks "how did you use Databricks", give the 20-second answer below, then point to the table.

## 20-second answer (optional, after slide 7)

"Everything runs on Databricks. The data lives in Unity Catalog. A Jobs workflow runs every morning at 6:00 AM and feeds a Lakeflow quality gate, the forecaster is tracked in MLflow and only registered if it beats two baselines, Model Serving scores it, and the planner app reads through a serverless SQL warehouse. Ask is a Genie space, and the storm desk uses a serving chat model that can only read."

## The Databricks services we used

| Service | What it does in StormSense | Where it lives |
|---|---|---|
| **Unity Catalog** | Governs the `stormsense` schema. The forecaster is registered as a model with the `champion` alias. | `databricks/notebooks/04_train_register.py` |
| **Delta tables** | About 15 tables: stores, products, sales, stock, weather, features, predictions, inventory gaps, transfer recommendations, audit, app users, feedback and route preferences. | `databricks/` (data bundle) |
| **Lakeflow pipeline** | "Data quality gates": a serverless pipeline that drops bad rows before features are built. | `databricks/pipelines/data_quality.sql` |
| **Jobs (Workflows)** | The daily 6:00 AM cycle, a build job, a storm trigger that checks NWS warnings every 15 minutes (paused by default), and the demo alert job. | `databricks/resources/jobs.yml` |
| **Serverless compute** | Notebooks and the pipeline run on serverless compute, so there are no clusters to manage. | Job and pipeline definitions |
| **MLflow** | Tracks the forecaster run: Poisson loss, validation window, features and metrics. | Experiment `/Shared/stormsense-demand-forecast` |
| **Model Serving** | The forecaster endpoint `stormsense-forecaster` (scale to zero) scores the what-if simulator. The storm desk calls a serving chat model, `databricks-gpt-5-mini`. | `backend/app/whatif.py`, `backend/app/agent.py` |
| **Serverless SQL warehouse** | Every planner screen reads through fixed, parameterised SQL. Approvals are guarded updates. | `backend/app/dbx.py` |
| **Genie** | The "Ask" space answers planner questions over a few tables. Read-only. | Space "StormSense Ask" |
| **Databricks Apps** | Defines the planner app as one process with its own service principal, linked to the warehouse and Genie. Defined, not yet deployed. | `backend/databricks.yml`, `backend/app.yaml` |
| **Asset Bundles (DABs)** | Deploys the data bundle and the app bundle from code. | `databricks/databricks.yml`, `backend/databricks.yml`, `make deploy` |
| **Lakeview dashboard** | "StormSense overview": deployed, not yet checked visually. | `databricks/dashboards/` |
| **Databricks SDK (Python)** | The API uses the SDK for SQL, Genie and serving calls. | `backend/app/sources/databricks.py` |

## How it works, step by step

**Each morning (Jobs, 6:00 AM Eastern)**
1. **Refresh weather:** the National Weather Service forecast is loaded per store into a Delta table.
2. **Data quality (Lakeflow):** rows that break the rules are dropped before anything else runs.
3. **Features:** built only from data that was known on that day, so the model never sees the future.
4. **Train and register:** the forecaster is trained on a time split (the last 28 days are held out). It is compared with two simple baselines. Only a model that beats both is registered in Unity Catalog with the `champion` alias. Each run is tracked in MLflow.
5. **Score:** the champion forecasts seven days for each store and product, and writes the predictions.
6. **Gaps:** projected stock and days of cover show where a store will run short, and when.
7. **Learn from feedback:** planners' rejection reasons adjust the route rankings for the next run. They never add or remove moves.
8. **Recommendations:** nearest-source matching proposes transfers. The write touches only pending rows. Decided rows are never overwritten.
9. **Verify:** the job fails loudly if anything is wrong, and emails the account that deployed it.

**When a planner uses the app**
- Screens read through the serverless SQL warehouse, with fixed, parameterised statements. The browser never calls Databricks.
- **Approve or reject** is a guarded update: it changes only rows that are still pending, and it writes an audit row for every attempt. A repeat approval is refused.
- **Ask** sends the question to the Genie space and returns one sentence with a table. It cannot change data.
- **What if** scores a normal week and a storm week with the serving endpoint, and changes nothing.
- **Storm desk** is a chat model with four read-only tools. Its plan may cite only transfers that a tool returned.

## Honest status for questions

- **Deployed and running:** the data bundle, the daily job, the forecaster, the Ask space and the local app against the workspace.
- **Defined, not yet deployed:** the Databricks App. Hosting is one command, but it has not been run in production.
- **Deployed, not visually checked:** the Lakeview dashboard.
- **Built, paused:** the storm trigger.
- **Not used:** Agent Bricks, AutoML and classic clusters.

---

# The whole story, end to end, in plain words

This section is for anyone who needs the business picture in plain language, including your own closing conversation. Every figure is sample data unless it says otherwise.

## 1. The problem in one picture

A storm is coming. Some stores will sell out of generators, tarps and pumps within days. Other stores, a region away, hold more of the same things than they can sell. Today a planner finds out too late, phones around, and the sales are lost. The store that ran out loses the sale, and the margin on it. The store with extra stock may end up discounting it later.

## 2. What the app does, step by step

1. **It reads three things for each store and product:** the weather forecast, the sales history, and the stock on hand.
2. **Every morning at 6:00 AM,** it predicts how much each product will sell over the next seven days.
3. **It checks the stock against the prediction.** Where stock will run out, it says which day. Where stock will sit unsold, it says so too.
4. **It proposes moves.** A store that will run short gets stock from the nearest store that has spare. Each proposal shows the reason, the sales it protects, and how confident the forecast is.
5. **It proposes markdowns** on surplus that would not sell at full price in time, with the cash it would bring in.
6. **Before a storm, it bundles the plan:** the moves, the markdowns, and a short note for each affected store.
7. **A planner decides.** They approve the moves they want and reject the rest in one step. Nothing moves without that approval.
8. **Trucks are shared where possible.** Moves on the same route can share one truck, which cuts trips.
9. **Afterwards, the impact page shows the result:** sales protected, margin, trucking cost, and the net. Rejections help the app rank routes better next time.

## 3. Who it helps, and what is in it for them

| Who | Their problem today | What StormSense gives them |
|---|---|---|
| **Store planner** | Late nights, phone calls, guesswork before a storm | One screen each morning, with the moves and their reasons |
| **Store manager** | Empty shelves in a storm and lost customers | Stock moved in before the storm, and a note for the store |
| **Operations or regional lead** | No view of where stock is short and where it is idle | One view of the whole network and the moves between stores |
| **Finance** | Lost margin, trucking spend, and surplus that is written down | Margin on protected sales, truck savings, and a record of every decision |
| **Customers** | Cannot buy what they came for | Products on the shelf when the storm arrives |
| **The business that owns it** | Lost sales, excess stock, and extra trucking | Recovered sales, less excess, fewer trucks, and lower CO₂ per move |

## 4. How the money works (sample figures)

| Item | Sample figure | What it means |
|---|---|---|
| Lost sales in five past storms and heat events | About $302,000 | Sales that were missed because stock was in the wrong store |
| Sales protected by the moves (current plan) | About $50,180 | Revenue the moves are expected to keep. This is a forecast, not a measurement |
| Margin on those sales (30% assumed) | About $15,054 | The profit part of the protected revenue |
| Trucking for the moves (about $2.50 a mile) | About $6,460 | The cost of moving the stock |
| **Net on the current sample plan** | **About $8,594** | Margin less trucking. This is the number to quote |
| Truck savings from sharing routes | About $2,000 | Fewer trips for the same moves |
| One markdown example (30 spare generators at 10% off) | About $260 more than holding | Cash recovered from surplus, if the estimated lift happens |

**The three things that drive the money:** protecting sales that would be lost, keeping margin on them, and spending less on trucks. Every item above is an estimate on sample data. The margin is an assumption. The protected sales are an upper bound from a backtest.

**Costs the business would carry:** the Databricks compute that runs the daily job, the forecast and the app. This has not been measured yet, so do not quote a running cost. Add it once measured.

## 5. How you would sell it (not decided yet)

The repository does not define a price or a business model. These are options to choose from, not decisions:

- **Per store, per month:** a fixed fee per store using the app. Simple to sell, but it does not link to results.
- **Per move or per storm:** a fee for each plan produced. Easy to explain, but it can feel like a tax on success.
- **Share of the verified net:** a fee taken only from measured recovered margin. Strongest value story, but needs a pilot to prove the numbers.
- **Pilot first, then a contract:** a fixed-price pilot in two or three stores against control stores, then a rollout if it beats the control.

**The recommended first step:** a paid pilot in a few stores, measured against control stores. It turns the sample numbers into real ones, and it gives you a price based on results.

## 6. What is honest about it today

- It runs on sample data. Real sales, stock and weather feeds are not connected yet.
- The forecast has an error of about 0.4 on sample data. It is good enough to rank the risks, not to predict exact units.
- It does not tell you what to buy. It moves and marks down stock you already have.
- It does not guarantee sales. It protects the sales it can, when stock exists to move.
- The Databricks App is defined but not deployed.

## 7. The one-minute closing conversation

Use this at the end of the demo, after the last question. Speak it in your own words, but keep the order.

> "Let me say it simply. Every morning StormSense looks at the weather, the sales and the stock in every store. It tells the planner which stores will run out, and which have stock sitting unused. Then it proposes the moves: take stock from the store that has it to the store that needs it, and mark down what would not sell in time. The planner approves or rejects each one, and every decision is recorded.
>
> Who gains? The planner gets one screen instead of phone calls. The store gets stock on the shelf before the storm. The business keeps the sales it would have lost, keeps the margin on them, and spends less on trucks.
>
> On our sample data, the proposed moves protect about fifty thousand dollars of revenue, which is about eight and a half thousand dollars of net after margin and trucking. That is an estimate, and it is an upper bound.
>
> How we would make money: we would start with a paid pilot in a few stores, measured against stores that do not use it. If the pilot proves the numbers, we charge for the rollout.
>
> What we need next: real sales and stock feeds, and the pilot. Thank you."

**If someone asks a quick question:**
- *"Does it buy stock?"* No. It moves and marks down stock that is already there.
- *"Does it guarantee sales?"* No. It protects the sales it can, when there is stock to move.
- *"What does it cost to run?"* We have not measured that yet. We will add it in the pilot.
- *"Is it live?"* It runs on sample data today. Real feeds and the deployment are the next steps.

---

# Suggested next idea: best sellers, and what comes next (not built)

**Status:** this is a suggestion for the future. It is **not built**, and this section does not claim otherwise. It is a natural next step because the app already forecasts units per store and product, and every product already knows which weather drives its sales.

## What the idea is, in plain words

Two questions a planner asks every week:

1. **"Which products will sell best in this weather?"** For example, if a heat wave is coming: coolers and pumps. If a storm: generators, tarps and plywood. The app would rank the products by the units it expects to sell in the stores under that weather.
2. **"What is likely to be next?"** The next weather pattern on the forecast, and which products usually respond to it. For example, after the heat wave, rain brings tarps and pumps forward.

The planner would see a short list, such as: "Next 7 days, heat is coming. Top sellers: coolers, pumps, fans. Stores to watch: Houston, Dallas, Austin."

## What is already there

- **Forecast by store and product:** the forecast gives seven days of units per store and product. Ranking those units gives a best-seller list for any week.
- **Weather drivers:** each product is tagged with the weather that moves its sales: wind, rain or heat. So "what responds to this weather" is already known for each product.
- **Weather forecast:** the National Weather Service forecast for each store feeds the daily run.

## What would need to be added

- **A ranking view:** sort the predicted units for the chosen stores and days. This is small, and it reads data the app already has.
- **A "next pattern" view:** match the coming weather to the products tagged with that driver, and show the ones forecast to rise.
- **A longer look:** the current forecast covers seven days. Anything beyond that needs a seasonal or trend model, which would be a separate project.

## How good it would be (honest view)

- **Good for:** deciding which stock to protect and move first, and which stores to watch. It turns the forecast into a short list a planner can act on.
- **Limits:** the forecast error is about 0.4 on sample data, so the ranking shows direction and order, not exact units. A weather pattern that does not match the history will be harder to predict.
- **Not a buying tool:** even this idea would not say what to buy. It would say which products to protect and move first from stock that exists.

## How to present it (20 seconds, optional, in Q&A or on slide 18)

> "A next step we have not built: the forecast already knows what will sell in each store. We would show the planner the top sellers for the weather coming, and which products usually follow it. That turns the forecast into a short list for the week. It's a suggestion for the future, and it uses data we already have."

**If asked whether it is built:** no. The forecast exists. The best-seller and "what's next" views are a suggestion.

---

# Easy starting points for the deck

Use these to start strong and stay on time. None of them changes the timing above.

## The first 15 seconds (use this exact shape)

1. **Look up, say your name.** "Good morning, I'm Adarsh Ajay."
2. **Name the problem in one sentence.** "Stores run out of stock in a storm, while stores nearby hold extra."
3. **Say what you built.** "StormSense moves stock before the storm, not after."
4. **Say the order.** "Four minutes on the idea and the numbers, then a live demo."

## Before you start (checklist)

- [ ] The app is open on `/today`, with the "Sample data" label visible.
- [ ] The deck is open in presenter view, with the timer showing.
- [ ] Screenshots from slide 6 are saved as a backup, in case the live demo fails.
- [ ] Your phone is on silent, and your laptop is on charge.
- [ ] You have read the script aloud once against a timer.
- [ ] You know the four numbers: $302,000 lost, 4% protected, $8,594 net, and 172 tests passing.

## Five tips that make the deck land

1. **One idea per slide.** If a slide has two points, cut one.
2. **Say the number, then what it means.** "Eight thousand five hundred dollars net. That is what we keep after margin and trucking."
3. **Point, don't read.** Point at the one thing you want them to look at.
4. **Pause after the key line.** Silence after "the wrong place" makes the point stick.
5. **Name your limits before judges do.** It makes everything else you say more believable.

## Phrases that sound confident and honest

- "On our sample data..."
- "This is an upper bound, so the real number is likely lower."
- "The planner stays in control. The system proposes, and the person decides."
- "We have not measured that yet. The pilot will."

---

# Last minute: the 8th-minute conclusion (after the demo)

**Time:** 1:00. This comes after the live demo, when you return to the slides. It makes the total 8 minutes: 4 for the presentation, 3 for the demo, and 1 for the close.

**Show:** slide 20 (Thank you), or a blank slide with one line: "Stock is already in the network. StormSense moves it to where it sells."

## The conclusion (say it at a steady pace, about 150 words)

> "Let me end where we started, in that store on a Thursday.
>
> The problem is not the weather. The weather is predictable. The problem is that the stock is in the wrong place, and nobody knows in time. That costs money in two ways: the sales we miss, and the margin we give up on them.
>
> StormSense fixes the timing. Every morning, it tells the planner which stores will run out, which have stock sitting unused, and what to move. The planner approves or rejects every move, and every decision is recorded.
>
> The value is simple to state. On our sample data, the proposed moves protect about fifty thousand dollars of revenue, and about eight and a half thousand dollars of net after margin and trucking. Trucks shared on the same route save about two thousand dollars more. Those are sample numbers, and they are an upper bound, so we will measure them, not just claim them.
>
> Here is what it means for each of you. The planner gets one screen instead of phone calls. The store keeps its customers. The business keeps the margin it would have lost, and spends less on trucks.
>
> The next step is small and measurable: a pilot in two or three stores, against stores that do not use it. If it beats the control, we scale. If it does not, we will know that too.
>
> Stock is already in the network. StormSense moves it to where it sells. Thank you."

## Points to remember for the close

- **Return to the Thursday store.** Starting and ending on the same picture makes the talk feel complete.
- **Say "sample" and "upper bound" once each, in this part.** Don't repeat them more than needed.
- **Give the pilot as the ask.** A clear next step is more persuasive than a big claim.
- **Stop talking after "Thank you".** Let questions come to you.

## If the demo went wrong

Skip the demo numbers in the conclusion. Say: "The live screens may have been slow, but the numbers are in the deck: about fifty thousand in protected sales, and eight and a half thousand in net, on sample data." Then deliver the same close.

---

**Total timing:** presentation 4:00 + demo 3:00 + conclusion 1:00 = **8:00**. If you only have 7 minutes, cut the conclusion to 30 seconds: keep the Thursday line, the net number, and "Thank you".

---

# End-to-end demo script (3:00)

Read this with the app open. The numbers on screen come from the sample data, and they can shift slightly when the sample dates roll forward. Always read what is on the screen, not the numbers in this script.

## Before you start (5 minutes before the talk)

1. **Stop any older server, then start the sample build.**
   - Run `make kill-ports`, then `make dev-sample`.
   - Use `make dev-sample`, not `make dev`. `make dev` uses the live workspace when `backend/.env` exists.
2. **Open two browser windows.**
   - Window A: `http://localhost:5173/` (the landing page).
   - Window B: `http://localhost:5173/transfers`. Keep this window on the Transfers screen. You will use it for the repeat-approval moment.
3. **Check the sample label.** Go to `/today` in window A. The header must show "Sample data".
4. **Do one rehearsal approval** on a different transfer, then restart `make dev-sample` so the demo starts clean.
5. **Keep the backups ready.** These screenshots are in `docs/screenshots/`:
   - `app-today-desktop.png`: the Today screen.
   - `app-transfers-approved.png`: after approval.
   - `app-store-forecast-desktop.png`: Store forecast.
   - `app-ask-idle-desktop.png`: Ask.
   - `app-history-desktop.png`: History.

## Timeline

| Clock | Step | Screen | Length |
|---|---|---|---|
| 0:00 | 1. Landing | `/` | 0:20 |
| 0:20 | 2. Today | `/today` | 0:30 |
| 0:50 | 3. Transfers: approve | `/transfers` | 0:50 |
| 1:40 | 4. Stores and Ask | `/stores`, then `/ask` | 0:45 |
| 2:25 | 5. History and the repeat approval | `/history`, then window B | 0:30 |
| 2:55 | 6. Hand back to the slides | Slide 20 | 0:05 |

---

## Step 1: Landing (0:00 to 0:20)

**Screen:** window A, `/`.

**Do:** scroll slowly, down about one screen. Let the 3D window and the animated transfers show. Scroll back up. Click **Open today's plan**.

**Say:** "This is the front door. It explains the idea in a few lines, and the planner app is one click away. I'll go straight in."

**Expect:** the storm scene and the headline "Move stock before the storm, not after."

**If it is slow:** click the **Open the planner** button in the navbar. It goes to the same place.

---

## Step 2: Today (0:20 to 0:50)

**Screen:** `/today`.

**Do:** point at the greeting, then the three numbers in the "Today at a glance" row.

**Say:** "This is the morning view. The greeting uses the planner's name. The first number is the urgent transfers this morning. The second is the stores running low. The third is the next weather alert, with the days it is expected. Everything on this screen is a planner's to-do list for today."

**Expect:**
- The greeting, with the name Ava.
- "urgent transfers" and "stores running low" with numbers above zero.
- A weather alert, such as a heat wave, with the days and the places it affects.

**Do:** point at the "Review transfers" button at the bottom. Click it.

**If the numbers are zero:** say "The sample data is quiet this morning, so here is what the screen does when there are urgent moves." Then click **Review transfers** anyway. It still goes to the Transfers page.

---

## Step 3: Transfers: approve two moves (0:50 to 1:40)

**Screen:** `/transfers`, window A.

**Do:**
1. Find the first urgent transfer. It reads like "Move 54 1000W generators from Jacksonville to Orlando".
2. Open it. Read its reason aloud. The reason says why it matters: the storm, what the store will sell, and what it has.
3. Select the first two urgent transfers.
4. At the bottom, click **Approve 2**.
5. In the dialog titled **Approve 2 transfers?**, click **Approve**.

**Say:** "This move is 54 generators, from Jacksonville to Orlando. The reason is in plain words: the storm on Sunday, how many Orlando will sell, and how many it has. Each move shows the sales it protects and how sure the forecast is. I'll select the first two and approve them."

**Expect:** a message: "2 transfers approved." The two moves leave the pending list.

**Say after the message:** "Approved. The system did the arithmetic. The planner made the decision, and the decision is recorded."

**If the dialog does not open:** press **Approve 2** again, or refresh the page and reselect the two moves.

---

## Step 4: Stores and Ask (1:40 to 2:25)

**Screen:** `/stores`, then `/ask`, window A.

**Do (Stores):**
1. Open **Store forecast**.
2. In the **Store** dropdown, choose **Orlando**. Its label shows how many products are running low.
3. Point at the bars for expected sales per day, and the chip that says when the product runs low.

**Say:** "This is the store view. Choose a store, and you see what it is likely to sell this week, day by day. The product that runs low is marked, with the day it runs out."

**Expect:** Orlando's 1000W generators, marked as running low on Thursday, with the bars for the week.

**Do (Ask):**
1. Click **Ask** in the sidebar.
2. Click the suggested question **Which stores will run out of generators this week?**, or type it into the box that says "Ask a question".

**Say:** "Ask is for questions in plain language. It answers in one sentence, with a small table. It cannot change anything."

**Expect:** one sentence, such as "2 stores will run low on 1000W generators this week, starting with Orlando on Thursday," and a table with the units short.

**If Ask is slow:** say "Ask runs a live query, so it can take a moment. Here is the answer from the screenshot," and show `app-ask-idle-desktop.png`.

---

## Step 5: History and the repeat approval (2:25 to 2:55)

**Screen:** `/history`, window A. Then window B.

**Do (History):**
1. Click **History** in the sidebar.
2. Point at the two approvals from Step 3. Each row shows the decision, who made it and when.

**Say:** "Every decision is recorded: what was decided, by whom, and when. That is the audit trail."

**Do (repeat approval, in window B):**
1. Switch to window B. It still shows the Transfers page from before you approved the moves in window A.
2. Select the same transfer you approved in Step 3.
3. Click **Approve 1**, then click **Approve** in the dialog.

**Say:** "Now another planner tries to approve the same move, from a screen that was open before. The system refuses it."

**Expect:** the message: "1 was already handled by someone else." Nothing changes.

**Say after the message:** "Double approval is harmless. The system checks the current state before it writes anything."

**If window B shows nothing to select:** the move was already approved in window A, which is the point. Say: "The move has already left the pending list, so the second planner sees it as handled." Then move on.

---

## Step 6: Hand back to the slides (2:55 to 3:00)

**Do:** switch to the deck, slide 20 (Thank you).

**Say:** "That's the whole loop: the morning view, a decision, the store and the question, and the record. Now the one-minute close."

**Then:** go straight into the 8th-minute conclusion from the script.

---

## If something fails

| Problem | What to do |
|---|---|
| The app does not load | Say "I'll show the screenshots," and open `app-today-desktop.png`. Walk through the same steps with the images. |
| The header does not show "Sample data" | You are on the live workspace. Stop the server with `make kill-ports`, then run `make dev-sample`. |
| No urgent transfers | Say "the sample data is quiet this morning." Go to Transfers and show one move from the list. |
| Approve gives an error | Refresh the page, reselect the moves and try once more. If it fails again, use `app-transfers-approved.png`. |
| Ask hangs | Show `app-ask-idle-desktop.png` and read the answer from the script. |
| Storm desk or what-if | Do not show them. They need the live workspace. |

## Words to say and words to avoid

- **Say:** "on the sample data", "the system proposes, the planner decides", "every decision is recorded".
- **Avoid:** "guaranteed", "the AI decides", "it buys stock", "live". The app is not live yet.
