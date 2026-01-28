# THE SCAMMER SHORT
**Version:** v2.0  
**Status:** Internal / Execution  
**Phase:** Paper Trading (Phase 0)

---

## 1. Overview

**THE SCAMMER SHORT** is a mechanical crypto-perpetuals trading system that exploits **mean reversion in extreme altcoin pumps** by **blindly shorting the Top 10 gainers** and exiting within a fixed 24-hour window.

The system is designed as a **betting machine**, not a predictive model.

---

## 2. Scope

| Item | Definition |
|---|---|
| Instruments | Perpetual futures (perps) only |
| Direction | Short-only |
| Market | Altcoins |
| Style | Basket mean reversion |
| Holding Period | Fixed 24 hours |
| Discretion | None in execution |

---

## 3. Supported Exchanges

| Phase | Exchanges |
|---|---|
| Phase 0 | Bitget |
| Expansion | Gate, KuCoin, Binance |

**Architecture**
- One independent bot instance per exchange
- No cross-exchange margining
- No inter-exchange hedging

**Bitget Account Rules (Phase 0)**
- Use a **dedicated subaccount** only
- **Configurable**: testnet vs real trading
- API permissions: **quotes, trading, transfers** (transfer is for future enhancement)
- IP whitelist: **future enhancement**

---

## 4. Trading Universe

| Rule | Definition |
|---|---|
| Instrument | USDT-M perpetuals |
| Selection | **Top 10 gainers by 24h % change** |
| Filters | **Max pump filter: include only > 15% (configurable)** |
| Veto Rules | **None** |
| Regime Filters | **None** |

---

## 5. Core Betting Strategy & Money Management (MASTER SECTION)

All risk, sizing, exits, and comparisons are defined **only here**.

---

### 5.1 Margin & Capital Model

| Parameter | Value |
|---|---|
| Margin Mode | **Cross** |
| Margin per Leg | **100 USDT** |
| Number of Legs | **10** |
| Total Margin at Risk | **1000 USDT** |
| Leverage | **3×** |
| Total Notional Exposure | **3000 USDT** |

**Notes**
- **Initial Investment** is a fixed baseline per run (paper or live).
  - Paper: `PAPER_INITIAL_BALANCE`
  - Live: `LIVE_INITIAL_BALANCE`
- **Total PnL** = realized + unrealized trading PnL (independent of deposits/withdrawals).
- **Current Balance / Equity** is exchange account equity (live) or simulated balance (paper).
- Percentages used for sizing/filters are **measured against total margin at risk**.
- Paper and Live runs are **independent** and may run in parallel with separate configs.

---

### 5.2 Entry Rules

| Rule | Definition |
|---|---|
| Entry Trigger | Operator-configured |
| Default Time | **04:00 UTC** (12:00 China time) |
| Entry Window | **Start within 60 minutes after entry time** |
| Frequency | Once per day |
| Execution | **Market orders**; blind short on all Top 10 gainers |
| Size Rounding | **Always round down** to valid exchange size |

Entry timing is configurable but **fixed per run**.

---

### 5.3 Exit Rules (Common to All Strategies)

| Rule | Definition |
|---|---|
| Hard Time Exit | **Close all positions at T + HOLD_HOURS** |
| Extension | Not allowed |
| Carry Positions | Not allowed |

---

## 6. Paper Trading Strategies (Phase 0)

All strategies:
- Use **identical entries**
- Use **identical prices**
- Differ **only in exit logic**

---

### Strategy S1 — Hard SL / Hard TP

| Rule | Value |
|---|---|
| Portfolio TP | Close all if **PnL > +30%** (+300 USDT) |
| Portfolio SL | Close all if **PnL < –30%** (–300 USDT) |
| Exit | Portfolio TP / Portfolio SL / **24h hard cutoff** |

Purpose: **Cap downside and lock wins**

---

### Strategy S2 — Raw 24h Only

| Rule | Value |
|---|---|
| Portfolio TP | None |
| Portfolio SL | None |
| Exit | **24h hard cutoff only** (or liquidation) |

Purpose: **Pure mean-reversion test**

**Notes**
- **No global kill switch** in S2 (true no‑SL mode).

---

### Strategy S3 — S1 + Trailing Leg Stop

| Rule | Value |
|---|---|
| Portfolio TP | Close all if **PnL > +30%** (+300 USDT) |
| Portfolio SL | Close all if **PnL < –30%** (–300 USDT) |
| Leg Trailing | If leg **PnL ≥ +100%**, apply **5% retracement** trailing stop on that leg |
| Exit | Portfolio TP / Portfolio SL / Trailing leg stop / **24h hard cutoff** |

Purpose: **Protect big winners while keeping the basket open**

---

## 7. Position Management Rules

| Rule | Definition |
|---|---|
| Order Safety | Reduce-only enforced on all closes |
| Position Flip | Forbidden |
| Partial Close | Allowed |
| Close-All | Supported (per exchange) |
| Manual Actions | Logged with source = UI |
| Global Kill Switch | **Close all if portfolio DD ≤ –30%** |

---

## 8. Market Data Polling & Persistence (UPDATED)

### Polling
| Item | Value |
|---|---|
| Price Source | Exchange mark price / last price |
| Polling Interval | **30 seconds** |
| Scope | All open legs |

### Persistence (NEW, LOCKED)
At **every poll**, the system **persists**:

- Timestamp
- Exchange
- Symbol
- Price
- Unrealized PnL (USDT)
- **Live only:** entry price, position size, margin used, leverage (all from exchange)
- Run ID

**Purpose**
- Crash / restart recovery
- Accurate DD and recovery analysis
- Offline replay of exit rules
- Future strategy comparison

**Notes**
- Full tick-level data is **not required**
- Poll-based snapshots are sufficient
- DB technology: **Supabase Postgres**
- **Live mode source of truth:** all stored values are pulled from Bitget, not configs
- Run metadata stores **initial investment** and **current balance** for UI/analytics

---

## 8.1 Backtest & Strategy Comparison (Planned)

Because snapshots are saved every 30s, the system will **replay** the same run to compare **S1 / S2 / S3** offline.

**Planned outputs**
- Per-strategy PnL and DD
- Exit reason and time
- Win rate and EV (later)

Backtest does **not** require live trading; it runs from stored snapshots.

---

## 9. Logging & Telemetry (Locked)

### Per Run (Daily)
- Run ID
- Exchange
- Entry time (UTC)
- Margin per leg
- Number of legs
- Leverage
- Strategy tag (paper only)
 - Order intent price vs actual execution price (entry/exit)
- Initial investment (fixed baseline)
- Current balance/equity (live)

### Per Leg (Coin)
- Symbol
- Entry price & timestamp
- Quantity
- Max favourable PnL (USDT)
- Max adverse PnL (USDT)
- Exit price & timestamp
- Exit reason:
  - 24h
  - leg TP
  - portfolio TP
  - portfolio SL

### Per Run Summary
- Max intraday DD (USDT, %)
- Time of max DD
- Final PnL (USDT, %)
- Duration
- Liquidation proximity flag (yes/no)

---

## 10. Web UI (Mandatory)

### Dashboard
- Real-time positions
- Per-leg & portfolio PnL
- Current balance/equity and used margin
- Max DD tracking
- Bot state (RUN / PAUSE)
- **LIVE tab uses exchange-backed values**
- **PAPER tab uses simulated values**

### Manual Controls
- Flatten all (reduce-only)
- Close individual leg (reduce-only)
- Pause / Resume bot
 - Manual TP/SL per leg

---

## 11. Tech Stack (Platforms – DB OPEN)

### UI / Frontend
| Layer | Platform |
|---|---|
| UI/UX | v0 |
| Framework | Next.js |
| Hosting | Vercel |
| Styling | Tailwind / shadcn |
| Realtime | WebSocket / DB-based |

### Backend / Bot
| Layer | Platform |
|---|---|
| Language | Python |
| API | FastAPI |
| Runtime | Railway (always-on worker, Phase 0) |
| Worker Size | 0.5 GB RAM / 1 vCPU |
| Scaling | Manual |

### Data Layer
| Item | Decision |
|---|---|
| Primary DB | **Supabase (Postgres)** |
| Time-series support | **Not needed (Phase 0)** |
| Snapshot Storage | Required |
| Auth | Optional (Phase 0 internal) |
| Retention | **Keep all data (no purge)** |

### Infra
| Layer | Platform |
|---|---|
| Containers | Docker |
| DNS / SSL | Cloudflare |
| Logs | Worker logs |

---

## 11.1 Phase 0 Hosting & Reliability Decisions (NEW)

**Railway usage (Phase 0 approved)**
- Railway is acceptable for Phase 0 **if the bot is restart-safe**
- Bot must tolerate restarts and reconnect without manual intervention
- Deploys should be **manual or scheduled**, not automatic during a live 24h run

**Required bot behaviors on Railway**
- **Boot recovery:** on start, load open positions + last poll timestamp from DB
- **Idempotent entry:** prevent duplicate entries by run_id + symbol + entry_time
- **Reconnect logic:** exponential backoff for exchange API/WS; fallback to REST if WS drops
- **Heartbeat:** write a heartbeat row every minute for UI health

**Database**
- Supabase Postgres is **cheap + reliable enough for Phase 0**
- Polling at 30s and ~28,800 rows/day is **trivial** for Postgres
- No Timescale or time-series add-on required in Phase 0

**Exchange abstraction**
- Start with **Bitget only**
- Use a **thin adapter layer** (minimal interface) but **no full abstraction** yet

---

## 12. Operating Principle

**THE SCAMMER SHORT** does not predict.  
It **accepts pain first** and measures whether **time destroys the pump**.

---

## 13. Phase 0 Objective

The goal of Phase 0 is **NOT profitability**.

The goal is to measure:
- Drawdown depth before recovery
- Recovery probability vs DD
- Cost of protection
- Value of tail harvesting

Only after data is collected are parameters adjusted.

---

## 14. New Feature List (Planned)

### 14.1 DB‑Backed Settings + Settings Page
- Move tunable runtime vars (paper/live strategy params) into DB.
- UI page to edit settings without redeploy.
- Keep secrets/infrastructure in Railway env.

### 14.2 Analytics & Reporting
**Metric definitions**
- **Initial Investment / Margin at Open:** fixed baseline at run start.
- **Final PnL (run/leg):** realized PnL only, scoped to that run.
- **Max DD (leg):** most negative unrealized PnL for that leg.
- **Max DD (run):** most negative aggregated unrealized PnL across all legs.
- **Peak PnL (leg):** highest unrealized PnL for that leg.
- **Peak PnL (run):** highest aggregated unrealized PnL across all legs.
- **Equity curve (chart):** Initial Investment + aggregated unrealized PnL.

**Run history (completed runs only)**
- Filters: date range, mode (paper/live), strategy (S1/S2/S3).
- Columns: run ID, mode, strategy, start/end, duration, close reason.
- Metrics per run: Initial Investment (margin at open), Final PnL (realized), Max DD, Peak PnL.

**Run drilldown (all legs)**
- Per‑leg metrics: Initial Investment, Final PnL (realized), Max DD, Peak PnL.

**Charts (per run)**
- Equity curve: Initial Investment + aggregated unrealized PnL.
- Lines: aggregate + individual legs (max 10 + 1 aggregate).

**Aggregates across runs**
- Percent only (simple average): Avg Final PnL %, Avg Max DD %, Avg Peak PnL %.
