# Environment Variables

## Runtime
- `APP_ENV`: local | staging | prod
- `EXCHANGE`: currently bitget
- `USE_TESTNET`: true | false
 - `MODE`: legacy (used only by worker_service); not used for paper/live separation

## Scheduling
- `ENTRY_TIME_UTC`: daily entry time (HH:MM)
- `TRADE_WEEKENDS`: true | false

## Strategy
- `NUM_LEGS`
- `MARGIN_PER_LEG_USDT`
- `LEVERAGE`
- `MAX_PUMP_PCT`
- `GLOBAL_KILL_DD_PCT`
- `POLL_INTERVAL_SEC`
- `STRATEGY_TAG` (S1 | S2 | S3)

## Independent Paper/Live Config (Preferred)
- `PAPER_STATUS`: on | off
- `LIVE_STATUS`: on | off
- `PAPER_*` and `LIVE_*` blocks mirror the base strategy settings above.
- Use these to run paper and live **in parallel** without conflict.
- `PAPER_INITIAL_BALANCE`: starting balance for paper trading (used for balance + DD)
- `LIVE_INITIAL_BALANCE`: required initial investment baseline for live trading (used for PnL/DD)

## Bitget (subaccount)
- `BITGET_API_KEY`
- `BITGET_API_SECRET`
- `BITGET_API_PASSPHRASE`
- `BITGET_BASE_URL`

## Supabase / Postgres
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL`

## API
- `API_PORT`
- `WORKER_HEARTBEAT_SEC`
