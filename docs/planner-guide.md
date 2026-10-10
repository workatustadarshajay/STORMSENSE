# Planner guide

This guide is for store planners. It explains each screen in plain words.

## Each morning

1. Open **Today**. It shows how many moves are urgent, how many are waiting for a decision, how many stores are at risk, and the next weather alert.
2. Select **Review moves** to go to **Transfers**.

## Transfers: approve or reject a move

Each move says:

- **What moves:** the product, how many, and from which store to which.
- **Why:** the reason in one or two sentences, including the weather.
- **Urgent or normal:** urgent moves are those where a store runs out within two days, or where the sales at risk are high.
- **How sure:** **High**, **Medium** or **Low**. This shows how much of the move is still needed if demand turns out lower than forecast.
- **Sales protected:** the money from sales that would be lost if the move did not happen.
- **About kg CO₂:** a planning estimate of the emissions for the trip, based on the distance and the share of a truck the move uses. It helps compare options. It isn't a measured figure.

To act:

1. Tick one or more moves, then select **Approve**. You can add a note.
2. To decline a move, select **Reject** and choose a reason: truck not available, store closed, already covered, route too slow, or other. The next morning's plan learns from it, so the same route is ranked lower next time. It doesn't remove the move from future plans.

Once a move is approved or rejected, the page shows who did it and when. If someone else has already handled it, you're told so and nothing changes.

## Today: storm readiness

Under the glance numbers, **Storm readiness** shows each store as one percentage: the share of its products with enough stock to last the storm window plus a safety margin of two days.

- **Ready** (80% or more): the store can get through the storm on its own stock.
- **Watch** (50% to 79%): some products will need a move.
- **At risk** (below 50%): most products run out inside the storm window.

Select a store to open its forecast.

## Today: price markdowns

Under the readiness list, **Price markdowns** suggests a discount for surplus stock that would not sell at full price in two weeks. A suggestion appears only when the discount brings in more cash than holding the stock. Each line gives the store, the product, the discount, and the cash it adds.

These are suggestions. Nothing changes until a store makes the price change. The estimate assumes that each 10% off lifts sales by 15%, so test it on a pilot before relying on it.

## Transfers: why a farther store is sending

When a move comes from a store that isn't the nearest, the reason says why in one line. For example: "Tampa is closer but also short of 1000W generators." The possible reasons are that the nearer store is also short, has no spare stock to send, or a planner rejected that route recently.

## Transfers: download or print the plan

**Download this week's plan (CSV)** opens the pending moves in a spreadsheet, with the reason, the sales protected and the estimated carbon for each. **Print or save as PDF** uses the browser's print dialog; choose "Save as PDF" to make a PDF for the store managers' meeting.

## Past storms

**History** links to **How past storms would have gone**. It replays each named storm in the history with the sales that really happened: the sales lost, and how much nearby stock could have covered. Read it as the best case, because it uses what really sold rather than the forecast.

## Stores

Pick a store to see its next seven days: expected sales for each product, the weather behind each day, and when the store is likely to run low.

## Ask

Type a question in plain words, for example "Which stores will run out of generators this week?" You get one sentence and, where it helps, a short table. Ask only reads; it can't change anything.

## Storm desk

From **Transfers**, select **Get a plan from storm desk** and describe your goal, for example "Prepare Florida for Sunday's storm". Storm desk checks the current stock, the weather and the pending moves, then writes a short plan. It names only moves that exist, and it never approves or changes anything. Select **How the crew reached this plan** to see each check it made. The risk checker also looks up what planners decided the last time the same route was used for the same product, and quotes the reason, for example "Last time this route was rejected because no truck was free."

## What if a storm comes?

From **Transfers**, select **What if a storm comes?**. Set how strong the storm is, when it hits, how many days it lasts, and where. You see:

- how many more units people are likely to buy,
- how much in sales would be lost if no stock moved,
- how much stock would need to move to prevent it.

These are estimates to plan with, not promises. Nothing is changed by this page.

## History

**History** lists every approval and rejection, with the person, the time and any note.

## Labels you will see

| Label | Meaning |
|---|---|
| Sample data | The sales and stock figures are sample data. The weather is live. |
| Urgent | A store is likely to run out within two days, or the sales at risk are high. |
| High, Medium, Low (confidence) | How much of the move is still needed if demand turns out lower than forecast. |
| Ranked lower | Planners have rejected a move on this route recently. It still appears, lower down. |

## If something looks wrong

Reject the move with the closest reason and add a note. The next daily plan takes that into account. If a number looks wrong, tell the team that runs StormSense, with the store and product name.

## Your uploads

Once a plan has been built from your files, the **Data shown** switch has a third choice, **Your uploads**. Today, Transfers, Stores and Storm desk then show that plan. The sidebar says **Your data**. The plan is a simple forecast from your last four weeks, not the trained model, and the upload app says so.

## Markdown approvals

On Today, a planner can **Approve** or **Reject** each price markdown suggestion. This records the decision and who made it. It does not change any prices in the stores.

## Analysis

**Analysis** shows the plan in pictures for whichever data is chosen: the demand expected each day against the stock available, the shortages by store, the moves by urgency, and the protected sales by product. Every chart has a **Show as a table** link with the same numbers.

## Business impact

**Business impact** shows what the plan is worth: the sales protected, the estimated margin, trucking and profit, and the estimated carbon. It also shows the decisions made so far, what has changed since the last plan, the assumptions behind the money figures, and a timeline of uploads, plans, cost changes and decisions, with who made each one. The money figures are estimates, not results.

## Morning briefing

The top of **Today** is your morning briefing: a headline and a few plain sentences. It says how many moves are urgent and waiting, the next weather alert, which stores are at risk and the least ready, the biggest move and what it protects, any markdowns to decide, and when stock was last counted. Every figure comes from the data you're looking at, so it follows the chosen source. It is not written by a model.

## Storm response

When a storm or heat warning is in the forecast, Today shows a **Storm response** card. It says how many moves are drafted for the storm and the sales they protect. **Review the storm response** opens the draft.

The draft holds the moves waiting for a decision, the open markdown suggestions, the carbon and the sales protected, and a draft note for each affected store. Nothing has been sent or moved. Tick the moves to keep, give a reason for the rest, and approve. The chosen moves are approved and the others are rejected, through the same approval path as every transfer, and the decision is recorded in the timeline. A decided response is not reopened.

The store notes are drafts only. Store email addresses are not set up yet, so nothing is sent to store managers.

