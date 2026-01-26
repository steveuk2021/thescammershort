# Environment Variables

## Runtime
- `APP_ENV`: local | staging | prod
- `MODE`: paper | live
- `EXCHANGE`: currently bitget
- `USE_TESTNET`: true | false

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
