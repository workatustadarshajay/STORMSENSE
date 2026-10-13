# Five-minute demo

## Before you start

1. Stop any older run first: `make kill-ports`.
2. Start the sample build with `make dev-sample`, not `make dev`. `make dev` uses the live workspace whenever `backend/.env` exists.
3. Open http://localhost:5173. You should see "Good morning, Ava" and the "Sample data" label.
4. For a rehearsal from a clean state, stop and restart `make dev-sample`. Approvals are kept in memory and reset on restart.

The "Sample data" label stays visible throughout; say so up front.

**1. The morning view (60 seconds).** Open *Today*. "Good morning, Ava" over a sky that has turned stormy: a tropical storm is expected Sunday on the Florida west coast. Three numbers: urgent transfers, stores running low, the next weather alert. One button: *Review transfers*.

**2. Decide in under two minutes (90 seconds).** *Transfers*. The urgent group reads as sentences: "Move 54 1000W generators from Jacksonville to Orlando". Read one reason aloud: the storm, what Orlando will sell, what it has. Point at the confidence words and the sales each move protects. Select the first two, tap *Approve 2*, confirm. The result reads "2 transfers approved."

**3. Why it works (60 seconds).** *Stores*, Orlando. Weather strip across the week, then each product's expected sales per day. The generators bar for Sunday is marked and the chip says "Runs low Thursday". The sentence underneath names the storm behind it.

**4. Ask in your own words (45 seconds).** *Ask*, tap "Which stores will run out of generators this week?" A sentence and a small table. Try "Which stores have extra stock?"

**5. Accountability (45 seconds).** *History* shows the two approvals, by whom and when. Open a second browser as another planner, try to approve the same transfer: "1 was already handled by someone else."

**Real data version.** Run the daily cycle first with `cd databricks && databricks bundle run stormsense_daily --profile stormsense`, then start the app against the workspace (`make dev`, with `backend/.env` in place) and show the same screens. Mention the 6:00 AM job and that the forecaster only goes live if it beats the simple baselines on the latest four weeks.

## If something goes wrong

| What you see | What to do |
|---|---|
| `Address already in use` | `make kill-ports`, then start again |
| The header or greeting is not Ava, or there is no "Sample data" label | You are on the live workspace. Stop it and run `make dev-sample` |
| Transfers already approved on the second run | Restart `make dev-sample` to reset |
| Storm desk or What if shows "not available" | Those need the live workspace. Skip them on sample data, or use the real-data version |
