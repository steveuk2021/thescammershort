from typing import Optional

import psycopg

from .db import get_conn
from .time_utils import now_utc


class RunRow:
    def __init__(self, run_id: str, status: str, start_ts: str, end_ts: Optional[str]) -> None:
        self.run_id = run_id
        self.status = status
        self.start_ts = start_ts
        self.end_ts = end_ts


def get_latest_run(mode: Optional[str] = None) -> Optional[RunRow]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if mode:
                cur.execute(
                    """
                    select run_id, status, start_ts::text, end_ts::text
                    from runs
                    where mode = %s
                    order by start_ts desc
                    limit 1
                    """,
                    (mode,),
                )
            else:
                cur.execute(
                    """
                    select run_id, status, start_ts::text, end_ts::text
                    from runs
                    order by start_ts desc
                    limit 1
                    """
                )
            row = cur.fetchone()
            if not row:
                return None
            return RunRow(row[0], row[1], row[2], row[3])


def get_active_run(mode: Optional[str] = None) -> Optional[RunRow]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if mode:
                cur.execute(
                    """
                    select run_id, status, start_ts::text, end_ts::text
                    from runs
                    where status in ('running', 'paused') and end_ts is null and mode = %s
                    order by start_ts desc
                    limit 1
                    """,
                    (mode,),
                )
            else:
                cur.execute(
                    """
                    select run_id, status, start_ts::text, end_ts::text
                    from runs
                    where status in ('running', 'paused') and end_ts is null
                    order by start_ts desc
                    limit 1
                    """
                )
            row = cur.fetchone()
            if not row:
                return None
            return RunRow(row[0], row[1], row[2], row[3])


def get_open_legs(run_id: str) -> list[tuple[str, float, float]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select symbol, entry_price, qty
                from legs
                where run_id = %s and status = 'open'
                """,
                (run_id,),
            )
            return cur.fetchall()


def get_legs(run_id: str) -> list[tuple]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select symbol, entry_price, exit_price, qty, status, exit_ts::text
                from legs
                where run_id = %s
                order by symbol asc
                """,
                (run_id,),
            )
            return cur.fetchall()


def get_run_balances(run_id: str) -> tuple[Optional[float], Optional[float]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select initial_balance, current_balance
                from runs
                where run_id = %s
                """,
                (run_id,),
            )
            row = cur.fetchone()
            if not row:
                return None, None
            return (float(row[0]) if row[0] is not None else None, float(row[1]) if row[1] is not None else None)


def create_run(
    run_id: str,
    exchange: str,
    mode: str,
    entry_time_utc: str,
    num_legs: int,
    margin_per_leg_usdt: float,
    leverage: float,
    max_pump_pct: float,
    global_kill_dd_pct: float,
    strategy_tag: str,
    initial_balance: Optional[float] = None,
    current_balance: Optional[float] = None,
) -> None:
    now = now_utc()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into runs (run_id, exchange, mode, entry_time_utc, start_ts, status, num_legs,
                                  margin_per_leg_usdt, leverage, max_pump_pct, global_kill_dd_pct, strategy_tag,
                                  initial_balance, current_balance)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    run_id,
                    exchange,
                    mode,
                    entry_time_utc,
                    now,
                    "running",
                    num_legs,
                    margin_per_leg_usdt,
                    leverage,
                    max_pump_pct,
                    global_kill_dd_pct,
                    strategy_tag,
                    initial_balance,
                    current_balance,
                ),
            )
        conn.commit()


def update_run_status(run_id: str, status: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                update runs set status = %s where run_id = %s
                """,
                (status, run_id),
            )
        conn.commit()


def update_run_balance(run_id: str, initial_balance: Optional[float] = None, current_balance: Optional[float] = None) -> None:
    if initial_balance is None and current_balance is None:
        return
    sets = []
    params: list[object] = []
    if initial_balance is not None:
        sets.append("initial_balance = %s")
        params.append(initial_balance)
    if current_balance is not None:
        sets.append("current_balance = %s")
        params.append(current_balance)
    params.append(run_id)
    set_clause = ", ".join(sets)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                update runs
                set {set_clause}
                where run_id = %s
                """,
                tuple(params),
            )
        conn.commit()


def end_run(run_id: str) -> None:
    now = now_utc()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                update runs set status = %s, end_ts = %s where run_id = %s
                """,
                ("completed", now, run_id),
            )
        conn.commit()


def insert_event(level: str, event_type: str, message: str, run_id: Optional[str] = None) -> None:
    now = now_utc()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into events (ts, level, type, message, run_id)
                values (%s, %s, %s, %s, %s)
                """,
                (now, level, event_type, message, run_id),
            )
        conn.commit()


def insert_leg(run_id: str, symbol: str, entry_price: float, qty: float) -> None:
    now = now_utc()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into legs (run_id, symbol, side, entry_price, entry_ts, qty, status)
                values (%s, %s, 'short', %s, %s, %s, 'open')
                """,
                (run_id, symbol, entry_price, now, qty),
            )
        conn.commit()


def upsert_live_leg(run_id: str, symbol: str, entry_price: float, qty: float) -> None:
    now = now_utc()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into legs (run_id, symbol, side, entry_price, entry_ts, qty, status)
                values (%s, %s, 'short', %s, %s, %s, 'open')
                on conflict (run_id, symbol)
                do update set
                    entry_price = excluded.entry_price,
                    qty = excluded.qty,
                    status = 'open',
                    exit_price = null,
                    exit_ts = null,
                    exit_reason = null,
                    entry_ts = case when legs.status = 'closed' then excluded.entry_ts else legs.entry_ts end,
                    max_favorable_pnl_usdt = case when legs.status = 'closed' then 0 else legs.max_favorable_pnl_usdt end,
                    max_adverse_pnl_usdt = case when legs.status = 'closed' then 0 else legs.max_adverse_pnl_usdt end
                """,
                (run_id, symbol, entry_price, now, qty),
            )
        conn.commit()


def update_leg_max(run_id: str, symbol: str, pnl_usdt: float) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                update legs
                set max_favorable_pnl_usdt = greatest(max_favorable_pnl_usdt, %s),
                    max_adverse_pnl_usdt = least(max_adverse_pnl_usdt, %s)
                where run_id = %s and symbol = %s
                """,
                (pnl_usdt, pnl_usdt, run_id, symbol),
            )
        conn.commit()


def update_leg_exit(run_id: str, symbol: str, exit_price: float, reason: str) -> None:
    now = now_utc()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                update legs
                set exit_price = %s, exit_ts = %s, exit_reason = %s, status = 'closed'
                where run_id = %s and symbol = %s
                """,
                (exit_price, now, reason, run_id, symbol),
            )
        conn.commit()


def insert_order(run_id: str, symbol: str, side: str, action: str,
                 intent_price: float, fill_price: float, qty: float, status: str) -> None:
    now = now_utc()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into orders (run_id, symbol, side, action, intent_price, fill_price, qty, status, ts)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (run_id, symbol, side, action, intent_price, fill_price, qty, status, now),
            )
        conn.commit()


def insert_snapshot(
    run_id: str,
    exchange: str,
    symbol: str,
    price: float,
    pnl: float,
    entry_price: Optional[float] = None,
    position_size: Optional[float] = None,
    margin_usdt: Optional[float] = None,
    leverage: Optional[float] = None,
) -> None:
    now = now_utc()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into snapshots (
                    ts, run_id, exchange, symbol, price, unrealized_pnl_usdt,
                    entry_price, position_size, margin_usdt, leverage
                )
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (now, run_id, exchange, symbol, price, pnl, entry_price, position_size, margin_usdt, leverage),
            )
        conn.commit()


def get_latest_command(ts_after: Optional[str] = None) -> Optional[tuple[str, str]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if ts_after:
                cur.execute(
                    """
                    select type, message from events
                    where type in ('command_pause', 'command_resume', 'command_close_all')
                      and ts > %s
                    order by ts desc
                    limit 1
                    """,
                    (ts_after,),
                )
            else:
                cur.execute(
                    """
                    select type, message from events
                    where type in ('command_pause', 'command_resume', 'command_close_all')
                    order by ts desc
                    limit 1
                    """
                )
            row = cur.fetchone()
            if not row:
                return None
            return row[0], row[1]
