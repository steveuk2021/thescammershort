# Database Schema (Phase 0)

This project uses a single Supabase Postgres database.

## Tables

### runs
- Tracks each daily run and its configuration snapshot.

### legs
- One row per symbol for a run (position lifecycle).

### orders
- Order intent vs actual execution for slippage tracking.

### snapshots
- 30-second polling snapshots: price + unrealized PnL.

### heartbeats
- Service health checks (worker/API).

### events
- Alerts, errors, and notable system actions.

### settings
- Runtime config values by mode (paper/live).

## Source of Truth
- Schema is defined in `backend/db/schema.sql`.
