# NEPSE data engine

- update_live_market.py fetches the public YONEPSE normalized market dataset, validates timestamps and stock rows, then writes data/live.json.
- generate_ai_signals.py calculates conservative short-term screening metrics and writes data/ai-signals.json.
- data_quality.py contains shared normalization and validation helpers.

The Actions workflow runs these scripts on a five-minute schedule during the Nepal market window. Scheduled GitHub Actions can be delayed; this is not a tick-by-tick feed. A stale-data guard in the dashboard blocks active trade calls when the source timestamp is older than 15 minutes.
