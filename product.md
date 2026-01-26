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
| Filters | **Max pump filter: exclude > 15% (configurable)** |
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
- Percentages are **always measured against total margin at risk**
- Equity balance, withdrawals, or deposits do **not** change the reference base

---

### 5.2 Entry Rules

| Rule | Definition |
|---|---|
| Entry Trigger | Operator-configured |
| Default Time | **04:00 UTC** (12:00 China time) |
| Frequency | Once per day |
| Execution | **Market orders**; blind short on all Top 10 gainers |
| Size Rounding | **Always round down** to valid exchange size |

Entry timing is configurable but **fixed per run**.

---

### 5.3 Exit Rules (Common to All Strategies)

| Rule | Definition |
|---|---|
| Hard Time Exit | **Close all positions at T + 24h** |
| Extension | Not allowed |
| Carry Positions | Not allowed |

---

## 6. Paper Trading Strategies (Phase 0)

All strategies:
- Use **identical entries**
- Use **identical prices**
- Differ **only in exit logic**

---

### Strategy 1 — Raw / Control

| Rule | Value |
|---|---|
| Leg TP | None |
| Portfolio TP | None |
| Portfolio SL | None |
| Exit | **24h hard cutoff only** |

Purpose: **Baseline behavior measurement**

---

### Strategy 2 — Harvest & Cap

| Rule | Value |
|---|---|
| Leg TP | Close leg if **PnL > +100% of margin** (+100 USDT) |
| Portfolio TP | Close all if **PnL > +30%** (+300 USDT) |
| Portfolio SL | None |
| Exit | Leg TP / Portfolio TP / 24h cutoff |

Purpose: **Capture tail winners + cap upside**

---

### Strategy 3 — Capital Protection

| Rule | Value |
|---|---|
| Leg TP | None |
| Portfolio TP | None |
| Portfolio SL | Close all if **PnL < –30%** (–300 USDT) |
| Exit | Portfolio SL / 24h cutoff |

Purpose: **Measure cost of protection**

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
- Equity & margin health
- Max DD tracking
- Bot state (RUN / PAUSE)

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
