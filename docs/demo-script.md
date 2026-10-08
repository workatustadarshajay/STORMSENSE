# Five-minute demo

Run it on sample data with `make dev` (open http://localhost:5173), or on the deployed app. The "Sample data" label stays visible throughout; say so up front.

**1. The morning view (60 seconds).** Open *Today*. "Good morning, Ava" over a sky that has turned stormy: a tropical storm is expected Sunday on the Florida west coast. Three numbers: urgent transfers, stores running low, the next weather alert. One button: *Review transfers*.

**2. Decide in under two minutes (90 seconds).** *Transfers*. The urgent group reads as sentences: "Move 54 1000W generators from Jacksonville to Orlando". Read one reason aloud: the storm, what Orlando will sell, what it has. Point at the confidence words and the sales each move protects. Select the first two, tap *Approve 2*, confirm. The result reads "2 transfers approved."

**3. Why it works (60 seconds).** *Stores*, Orlando. Weather strip across the week, then each product's expected sales per day. The generators bar for Sunday is marked and the chip says "Runs low Thursday". The sentence underneath names the storm behind it.

**4. Ask in your own words (45 seconds).** *Ask*, tap "Which stores will run out of generators this week?" A sentence and a small table. Try "Which stores have extra stock?"

**5. Accountability (45 seconds).** *History* shows the two approvals, by whom and when. Open a second browser as another planner, try to approve the same transfer: "1 was already handled by someone else."

**Real data version.** Before the demo run `make deploy` (or `bundle run stormsense_daily`) and show the same screens on the Databricks App. Mention the 6:00 AM job and that the forecaster only goes live if it beats the simple baselines on the latest four weeks.
