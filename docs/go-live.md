# Go-live checklist

The app is built to run unchanged on real data. Work through this list before planners rely on it.

**Data**
- [ ] Replace the four sample feed tables (`sales_history`, `inventory_snapshot`, `weather_observed`, and the stores and products dimensions) with feeds from the real systems. Keep the column names; see `data-dictionary.md`.
- [ ] Add a daily task ahead of `refresh_weather` that lands yesterday's sales and today's stock count. The forecast origin is the latest stock date.
- [ ] Remove the `data_label` row from `settings` so the "Sample data" label disappears.
- [ ] Re-run the build job so the forecaster is trained and checked on real history. It is promoted only if it beats both baselines.
- [ ] Review the thresholds in `settings` with the planners (safety days, surplus days, distance, minimum quantity).

**Weather**
- [ ] Deploy with `weather_provider=nws` (US stores) or add another provider in `stormsense_core/weather.py`; the task fails loudly if the provider is unavailable.
- [ ] Switch the provider's day boundaries to each store's time zone (`parse_nws_grid` currently uses UTC days).

**Access and security**
- [ ] Add every planner and viewer to `app_users` and give them Can use on the app. Remove the default admin if it was a personal account.
- [ ] Confirm the app's service principal has only the grants made by the `stormsense_app_access` job.
- [ ] Use a company service principal for deployments from CI instead of a personal login.
- [ ] HTTPS is provided by Databricks Apps. If you also run the container image elsewhere, put it behind HTTPS and the company's sign-in.
- [ ] Secrets: none are stored. Keep it that way; use a secret scope for any future provider key.

**Reliability**
- [ ] Add a second recipient to the job's failure emails (a shared mailbox), or a webhook notification.
- [ ] Add a job duration warning and an alert on the `model_runs` table when the forecaster does not beat the baselines.
- [ ] Back up: Delta tables have time travel; set a retention that matches policy and export `transfer_audit` regularly.
- [ ] Monitoring: watch `databricks apps logs`, warehouse query history, and the daily job's run history.

**Process**
- [ ] Run `make smoke` against the production workspace and keep the output.
- [ ] Agree who owns the daily failure email and who can edit `settings`.
