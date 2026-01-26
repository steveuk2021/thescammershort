# THE SCAMMER SHORT — Architecture (Phase 0)

## 1. Purpose
Phase 0 is a test harness to evaluate the trading theory with adjustable parameters, full telemetry, and both paper + live execution against Bitget.

## 2. High-Level Components
- **Worker (Python)**: strategy loop, market data polling, order execution, risk controls.
- **API (FastAPI)**: UI reads state + sends commands (pause/resume, manual TP/SL, close).
- **UI (Next.js on Vercel)**: dashboard and manual controls, Bitget-like layout.
- **Database (Supabase Postgres)**: source of truth for runs, legs, orders, snapshots, and heartbeats.

## 3. Data Flow
1. Worker starts run at configured UTC time.
2. Worker pulls top gainers, applies filters, submits market orders.
3. Worker polls price every 30s, persists snapshots + PnL.
4. API serves current state from DB; UI renders real-time panels.
5. UI control actions -> API -> Worker command queue (or direct DB flags).
6. Run ends by 24h cutoff or global kill switch.

## 4. Bot Process Model
- **Two services**: trading worker + API server.
- Worker is restart-safe and resumes from DB.
- API is read-heavy; no trading logic.

## 5. Execution Rules (Phase 0)
- **Exchange**: Bitget only, dedicated subaccount.
- **Mode**: configurable testnet vs real.
- **Orders**: market orders only.
- **Sizing**: always round down to valid exchange size.
- **Max pump filter**: exclude symbols > 15% (configurable).
- **Global kill switch**: close all if portfolio DD <= –30%.
- **Hold time**: fixed 24 hours, no extensions.

## 6. Logging & Telemetry
- Persist price + PnL snapshots every 30s (keep all data).
- Record order intent price and actual execution price.
- Heartbeat row every minute for UI health.
- Alerts: dashboard + debug log only (Phase 0).

## 7. UI Requirements (Phase 0)
- Real-time positions
- Per-leg position and PnL
- Margin + overall PnL
- Overall DD
- Run status
- Pause/Resume
- Manual TP/SL per leg
- Bitget-like layout and flow

## 8. Database (Supabase Postgres)
Single database for all data.

**Core tables (draft)**
- `runs`: run_id, exchange, mode, entry_time, strategy, status, start/end.
- `legs`: run_id, symbol, entry_price, qty, exit_price, exit_reason.
- `orders`: run_id, symbol, side, intent_price, fill_price, status, ts.
- `snapshots`: ts, run_id, exchange, symbol, price, u_pnl.
- `heartbeats`: ts, service, status.
- `events`: ts, type, message, run_id, symbol (optional).

## 9. Deployment & Secrets
- GitHub auto-deploy to Railway.
- Secrets in Railway env vars.
- Local dev uses `.env`.

## 10. Open Items
- Exact UI layout and data refresh cadence.
- Detailed schema (indexes, constraints).
- Command channel for API -> Worker (DB flags vs message queue).
