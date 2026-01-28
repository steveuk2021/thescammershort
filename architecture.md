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
   - Live mode writes **exchange fields** (entry, size, margin, leverage).
4. Worker records **initial investment** at run start and updates **current balance** during polls.
5. API serves current state from DB; UI renders real-time panels.
6. UI control actions -> API -> Worker command queue (or direct DB flags).
7. Run ends by 24h cutoff or global kill switch.

## 4. Bot Process Model
- **Two services**: trading worker + API server.
- Worker is restart-safe and resumes from DB.
- API is read-heavy; no trading logic.
- **Paper and Live are independent**: separate configs and run streams.
- **Initial investment** is set via `PAPER_INITIAL_BALANCE` / `LIVE_INITIAL_BALANCE`.
- **Current balance** for live is pulled from Bitget account equity.

## 5. Execution Rules (Phase 0)
- **Exchange**: Bitget only, dedicated subaccount.
- **Mode**: configurable testnet vs real.
- **Orders**: market orders only.
- **Sizing**: always round down to valid exchange size.
- **Max pump filter**: include only symbols > 15% (configurable).
- **Global kill switch**: close all if portfolio DD <= –30%.
- **Hold time**: configurable via `HOLD_HOURS` (default 24), no extensions.
- **Entry window**: start within 60 minutes after entry time.

## 5.1 Strategy Set (Phase 0)
- **S1**: hard portfolio TP (+30%) and SL (–30%), otherwise 24h cutoff.
- **S2**: no TP/SL, close at 24h cutoff (or liquidation).
- **S3**: S1 + trailing stop on any leg after +100% PnL with 5% retracement.

## 6. Logging & Telemetry
- Persist price + PnL snapshots every 30s (keep all data).
- Record order intent price and actual execution price.
- Heartbeat row every minute for UI health.
- Alerts: dashboard + debug log only (Phase 0).
- **Live reconciliation:** DB legs are synced against Bitget positions every poll.

## 6.1 Backtest & Strategy Comparison (Planned)
- Replay stored snapshots to evaluate **S1/S2/S3** on the same run.
- Output per-strategy PnL, DD, and exit timing.

## 7. UI Requirements (Phase 0)
- Real-time positions
- Per-leg position and PnL
- Current balance + used margin
- Total PnL (realized + unrealized)
- Overall DD
- Run status
- Pause/Resume
- Manual TP/SL per leg
- Bitget-like layout and flow

## 8. Database (Supabase Postgres)
Single database for all data.

**Core tables**
- `runs`: run_id, exchange, mode, entry_time, strategy, status, start/end, initial_balance, current_balance.
- `legs`: run_id, symbol, entry_price, qty, exit_price, exit_reason.
- `orders`: run_id, symbol, side, intent_price, fill_price, status, ts.
- `snapshots`: ts, run_id, exchange, symbol, price, u_pnl.
- `heartbeats`: ts, service, status.
- `events`: ts, type, message, run_id, symbol (optional).

Schema source: `backend/db/schema.sql`

## 9. Deployment & Secrets
- GitHub auto-deploy to Railway.
- Secrets in Railway env vars.
- Local dev uses `.env`.

## 10. Open Items
- Exact UI layout and data refresh cadence.
- Detailed schema (indexes, constraints).
- Command channel for API -> Worker (DB flags vs message queue).
