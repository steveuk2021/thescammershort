# THE SCAMMER SHORT — Project Plan (Phase 0)

## Plan Rules
- This plan is the single source of truth.
- Execute steps in order; do not skip.
- Changes to plan must be explicit in this file.

## Phase 0 Implementation Plan
1. **[DONE] Project bootstrap**
   - Initialize repo structure.
   - Add config templates and environment docs.

2. **[NEXT] Database design**
   - Finalize schema for runs, legs, orders, snapshots, heartbeats, events.
   - Create migrations for Supabase Postgres.

3. **Exchange integration (Bitget)**
   - Implement market data fetch.
   - Implement order placement + close.
   - Implement account/position fetch.

4. **Core strategy engine**
   - Entry logic (top gainers + filters).
   - Exit logic (24h cutoff, TP/SL variants, global DD kill switch).
   - Size calculation + rounding down.

5. **State + telemetry**
   - Poll loop (30s) + snapshot persistence.
   - Run/leg/order logging.
   - Heartbeat + event logs.

6. **Worker service**
   - Scheduler for daily run (UTC).
   - Restart-safe boot recovery.
   - Safe command handling (pause/resume/close).

7. **API service (FastAPI)**
   - Read endpoints for UI (positions, PnL, DD, status).
   - Control endpoints (pause/resume, manual TP/SL, close).

8. **Web UI (Next.js)**
   - Dashboard panels (positions, PnL, margin, DD, status).
   - Controls (pause/resume, manual TP/SL).
   - Bitget-like layout.

9. **Paper trading mode**
   - Simulated fills + slippage logging.
   - Same telemetry as live.

10. **Live trading mode**
    - Configurable toggle (paper vs live).
    - Exchange order permissions verified.

11. **Operational readiness**
    - Config + secrets management.
    - Deploy pipeline (GitHub → Railway).
    - Basic alert surfaces (dashboard + debug log).

12. **Validation**
    - Dry run on testnet.
    - Confirm logs, UI, and recovery.
