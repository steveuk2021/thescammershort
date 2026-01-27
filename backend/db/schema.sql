-- Phase 0 schema for Supabase Postgres

create extension if not exists "uuid-ossp";

-- Runs
-- Runs: one row per daily execution
create table if not exists runs (
  run_id uuid primary key default uuid_generate_v4(),
  exchange text not null, -- exchange name (bitget)
  mode text not null check (mode in ('paper', 'live')), -- run mode
  entry_time_utc time not null, -- scheduled entry time (UTC)
  start_ts timestamptz not null, -- actual run start timestamp
  end_ts timestamptz, -- actual run end timestamp
  status text not null check (status in ('scheduled', 'running', 'paused', 'completed', 'stopped')), -- run lifecycle
  strategy_tag text, -- which paper strategy variant (optional)
  num_legs int not null, -- number of symbols to short (default 10)
  margin_per_leg_usdt numeric(18,8) not null, -- margin allocated per leg
  leverage numeric(10,4) not null, -- leverage used for the run
  max_pump_pct numeric(10,6) not null, -- filter: exclude > X% 24h pump
  global_kill_dd_pct numeric(10,6) not null, -- kill switch threshold (portfolio DD)
  initial_balance numeric(18,8), -- account equity at run start (live) or configured (paper)
  current_balance numeric(18,8), -- latest account equity (live) or simulated (paper)
  notes text -- free-form notes
);

-- Legs (positions per symbol)
-- Legs: one row per symbol per run
create table if not exists legs (
  leg_id uuid primary key default uuid_generate_v4(),
  run_id uuid not null references runs(run_id) on delete cascade, -- parent run
  symbol text not null, -- e.g. DOGEUSDT
  side text not null check (side in ('short')), -- always short in Phase 0
  entry_price numeric(18,8), -- actual average fill price on entry
  entry_ts timestamptz, -- entry time
  qty numeric(18,8), -- position size after rounding down
  exit_price numeric(18,8), -- actual average fill price on exit
  exit_ts timestamptz, -- exit time
  exit_reason text check (exit_reason in ('24h', 'leg_tp', 'portfolio_tp', 'portfolio_sl', 'manual', 'kill_switch')), -- why we exited
  max_favorable_pnl_usdt numeric(18,8) default 0, -- best unrealized PnL
  max_adverse_pnl_usdt numeric(18,8) default 0, -- worst unrealized PnL
  status text not null check (status in ('open', 'closed')), -- position state
  unique (run_id, symbol)
);

-- Orders (intent vs fill)
-- Orders: intent vs fill for slippage tracking
create table if not exists orders (
  order_id uuid primary key default uuid_generate_v4(),
  run_id uuid not null references runs(run_id) on delete cascade, -- parent run
  symbol text not null, -- symbol for the order
  side text not null check (side in ('sell', 'buy')), -- sell to open short, buy to close short
  action text not null check (action in ('open', 'close')), -- open or close
  intent_price numeric(18,8), -- intended price at submission
  fill_price numeric(18,8), -- actual average fill price
  qty numeric(18,8), -- order quantity
  status text not null check (status in ('submitted', 'filled', 'rejected', 'canceled')), -- order state
  exchange_order_id text, -- exchange order id
  ts timestamptz not null -- order timestamp
);

-- 30s snapshots (price + PnL)
-- Snapshots: 30s polling data for each open leg
create table if not exists snapshots (
  snapshot_id uuid primary key default uuid_generate_v4(),
  ts timestamptz not null, -- snapshot time
  run_id uuid not null references runs(run_id) on delete cascade, -- parent run
  exchange text not null, -- exchange name
  symbol text not null, -- symbol
  price numeric(18,8) not null, -- mark/last price at poll
  unrealized_pnl_usdt numeric(18,8) not null, -- unrealized PnL at poll
  entry_price numeric(18,8), -- average entry price from exchange (live) or simulated (paper)
  position_size numeric(18,8), -- live position size (contracts/units)
  margin_usdt numeric(18,8), -- live margin used for this position
  leverage numeric(10,4) -- live leverage for this position
);

-- Heartbeats
-- Heartbeats: health pings for services
create table if not exists heartbeats (
  heartbeat_id uuid primary key default uuid_generate_v4(),
  ts timestamptz not null, -- ping time
  service text not null, -- worker or api
  status text not null check (status in ('ok', 'degraded')), -- health status
  message text -- optional details
);

-- Events (alerts, errors, notable actions)
-- Events: alerts, errors, and notable actions
create table if not exists events (
  event_id uuid primary key default uuid_generate_v4(),
  ts timestamptz not null, -- event time
  level text not null check (level in ('info', 'warn', 'error')), -- severity
  type text not null, -- event type label
  message text not null, -- event details
  run_id uuid references runs(run_id) on delete set null, -- optional run link
  symbol text -- optional symbol link
);

-- Indexes
create index if not exists idx_snapshots_run_ts on snapshots(run_id, ts);
create index if not exists idx_orders_run_ts on orders(run_id, ts);
create index if not exists idx_legs_run on legs(run_id);
create index if not exists idx_events_run_ts on events(run_id, ts);
