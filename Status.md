# THE SCAMMER SHORT — Project Plan (Phase 0)

## Plan Rules
- This plan is the single source of truth.
- Execute steps in order; do not skip.
- Changes to plan must be explicit in this file.

## Phase 0 Implementation Plan
1. **[DONE] Project bootstrap**
    - Initialize repo structure.
    - Add config templates and environment docs.
    - Validation: confirm files/directories created and docs updated.

2. **[DONE] Database design**
    - Finalize schema for runs, legs, orders, snapshots, heartbeats, events.
    - Create migrations for Supabase Postgres.
    - Validation: apply schema in Supabase; verify 6 tables created.

3. **[DONE] Exchange integration (Bitget)**
    - Implement market data fetch.
    - Implement order placement + close.
    - Implement account/position fetch.
    - Validation: run a basic API smoke test (tickers + positions) with testnet keys.

4. **[DONE] Core strategy engine**
    - Entry logic (top gainers + filters).
    - Exit logic for S1/S2/S3 (24h cutoff, hard TP/SL, trailing leg stop).
    - Size calculation + rounding down.
    - Validation: dry-run simulation against stored tickers.

5. **[DONE] State + telemetry**
    - Poll loop (30s) + snapshot persistence.
    - Run/leg/order logging.
    - Heartbeat + event logs.
    - Validation: insert + read sample rows in DB.

6. **[DONE] Worker service**
    - Scheduler for daily run (UTC).
    - Restart-safe boot recovery.
    - Safe command handling (pause/resume/close).
    - Validation: restart worker and confirm resume behavior.

7. **[DONE] API service (FastAPI)**
    - Read endpoints for UI (positions, PnL, DD, status).
    - Control endpoints (pause/resume, manual TP/SL, close).
    - Validation: hit endpoints locally and verify responses.

8. **[DONE] Web UI (Next.js)**
    - Dashboard panels (positions, PnL, margin, DD, status).
    - Controls (pause/resume, manual TP/SL).
    - Bitget-like layout.
    - Balance semantics: Initial Investment + Current Balance + trading PnL + true DD.
    - Validation: verify dashboard renders live DB data.

9. **[PENDING FINAL VALIDATION] Paper trading mode**
    - Simulated fills + slippage logging.
    - Same telemetry as live.
    - Validation: compare paper fills vs expected.

10. **[PENDING FINAL VALIDATION] Live trading mode**
    - Configurable toggle (paper vs live).
    - Exchange order permissions verified.
    - LIVE_INITIAL_BALANCE required for live runs.
    - Validation: small live trade on subaccount.

11. **Operational readiness**
    - Config + secrets management.
    - Deploy pipeline (GitHub → Railway + Vercel).
    - Services: API + Paper trader + Live trader (no worker service).
    - Basic alert surfaces (dashboard + debug log).
    - Validation: deploy and confirm API health + paper/live heartbeats.

12. **Validation**
    - Dry run on testnet.
    - Confirm logs, UI, and recovery.

13. **Backtest & Strategy Comparison**
    - Replay stored snapshots for S1/S2/S3.
    - Output per-strategy PnL/DD/exit timing.
