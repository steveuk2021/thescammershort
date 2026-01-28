import base64
import os
from fastapi import FastAPI, Header, HTTPException
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

from backend.common.db import get_conn
from backend.common.config import RuntimeSettings, settings
from backend.common.db_ops import get_settings, upsert_settings
from backend.common.db_ops import get_legs

app = FastAPI(title="The Scammer Short API")

# Allow local UI to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://thescammershort.vercel.app"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_settings_auth(authorization: str | None) -> None:
    user = os.getenv("SETTINGS_USER", "")
    pw = os.getenv("SETTINGS_PASS", "")
    if not user or not pw:
        raise HTTPException(status_code=500, detail="Settings auth not configured")
    if not authorization or not authorization.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1].strip()
    try:
        decoded = base64.b64decode(token).decode("utf-8")
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if ":" not in decoded:
        raise HTTPException(status_code=401, detail="Unauthorized")
    u, p = decoded.split(":", 1)
    if u != user or p != pw:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def health():
    return {"status": "ok"}


def _get_hold_hours_for_mode(mode: str) -> float:
    prefix = "PAPER" if mode == "paper" else "LIVE"
    runtime = RuntimeSettings(prefix, mode, settings)
    overrides = get_settings(mode)
    if overrides:
        runtime.apply_overrides(overrides)
    return runtime.hold_hours


@app.get("/settings")
def get_runtime_settings(mode: str, authorization: str | None = Header(default=None)):
    _require_settings_auth(authorization)
    return {"mode": mode, "settings": get_settings(mode)}


@app.put("/settings")
def put_runtime_settings(mode: str, payload: dict, authorization: str | None = Header(default=None)):
    _require_settings_auth(authorization)
    settings_map = payload.get("settings", {})
    if not isinstance(settings_map, dict):
        raise HTTPException(status_code=400, detail="Invalid settings payload")
    upsert_settings(mode, settings_map)
    return {"ok": True}


@app.get("/runs/latest")
def get_latest_run(mode: str = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            if mode:
                cur.execute(
                    """
                    select run_id, exchange, mode, entry_time_utc::text, start_ts::text, end_ts::text, status,
                           num_legs, margin_per_leg_usdt, leverage, max_pump_pct, global_kill_dd_pct, strategy_tag,
                           initial_balance, current_balance
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
                    select run_id, exchange, mode, entry_time_utc::text, start_ts::text, end_ts::text, status,
                           num_legs, margin_per_leg_usdt, leverage, max_pump_pct, global_kill_dd_pct, strategy_tag,
                           initial_balance, current_balance
                    from runs
                    order by start_ts desc
                    limit 1
                    """
                )
            row = cur.fetchone()
            if not row:
                return {"run": None}
            run_mode = row[2]
            return {
                "run": {
                    "run_id": row[0],
                    "exchange": row[1],
                    "mode": run_mode,
                    "entry_time_utc": row[3],
                    "start_ts": row[4],
                    "end_ts": row[5],
                    "status": row[6],
                    "num_legs": row[7],
                    "margin_per_leg_usdt": float(row[8]),
                    "leverage": float(row[9]),
                    "max_pump_pct": float(row[10]),
                    "global_kill_dd_pct": float(row[11]),
                    "strategy_tag": row[12],
                    "initial_balance": float(row[13]) if row[13] is not None else None,
                    "current_balance": float(row[14]) if row[14] is not None else None,
                    "hold_hours": float(_get_hold_hours_for_mode(run_mode)),
                }
            }


@app.get("/positions/open")
def get_open_positions(run_id: str = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            latest_run_id = run_id
            if not latest_run_id:
                cur.execute(
                    """
                    select run_id
                    from runs
                    order by start_ts desc
                    limit 1
                    """
                )
                run_row = cur.fetchone()
                if not run_row:
                    return {"positions": []}
                latest_run_id = run_row[0]
            cur.execute(
                """
                select symbol, entry_price, qty, status, max_favorable_pnl_usdt, max_adverse_pnl_usdt
                from legs
                where status = 'open' and run_id = %s
                order by symbol asc
                """,
                (latest_run_id,),
            )
            rows = cur.fetchall()
            return {
                "positions": [
                    {
                        "symbol": r[0],
                        "entry_price": float(r[1]) if r[1] is not None else None,
                        "qty": float(r[2]) if r[2] is not None else None,
                        "status": r[3],
                        "max_favorable_pnl_usdt": float(r[4]) if r[4] is not None else 0.0,
                        "max_adverse_pnl_usdt": float(r[5]) if r[5] is not None else 0.0,
                    }
                    for r in rows
                ]
            }


@app.get("/legs")
def get_legs_for_run(run_id: str = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            latest_run_id = run_id
            if not latest_run_id:
                cur.execute(
                    """
                    select run_id
                    from runs
                    order by start_ts desc
                    limit 1
                    """
                )
                run_row = cur.fetchone()
                if not run_row:
                    return {"legs": []}
                latest_run_id = run_row[0]
    rows = get_legs(latest_run_id)
    return {
        "legs": [
            {
                "symbol": r[0],
                "entry_price": float(r[1]) if r[1] is not None else None,
                "exit_price": float(r[2]) if r[2] is not None else None,
                "qty": float(r[3]) if r[3] is not None else None,
                "status": r[4],
                "exit_ts": r[5],
            }
            for r in rows
        ]
    }


@app.get("/snapshots/latest")
def get_latest_snapshots(limit: int = 50, run_id: str = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            latest_run_id = run_id
            if not latest_run_id:
                cur.execute(
                    """
                    select run_id
                    from runs
                    order by start_ts desc
                    limit 1
                    """
                )
                run_row = cur.fetchone()
                if not run_row:
                    return {"snapshots": []}
                latest_run_id = run_row[0]
            cur.execute(
                """
                select ts::text, run_id, exchange, symbol, price, unrealized_pnl_usdt,
                       entry_price, position_size, margin_usdt, leverage
                from snapshots
                where run_id = %s
                order by ts desc
                limit %s
                """,
                (latest_run_id, limit),
            )
            rows = cur.fetchall()
            return {
                "snapshots": [
                    {
                        "ts": r[0],
                        "run_id": r[1],
                        "exchange": r[2],
                        "symbol": r[3],
                        "price": float(r[4]),
                        "unrealized_pnl_usdt": float(r[5]),
                        "entry_price": float(r[6]) if r[6] is not None else None,
                        "position_size": float(r[7]) if r[7] is not None else None,
                        "margin_usdt": float(r[8]) if r[8] is not None else None,
                        "leverage": float(r[9]) if r[9] is not None else None,
                    }
                    for r in rows
                ]
            }


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


@app.get("/reports/runs")
def get_report_runs(
    mode: str | None = None,
    strategy: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    clauses = ["status = 'completed'"]
    params: list[object] = []
    if mode:
        clauses.append("mode = %s")
        params.append(mode)
    if strategy:
        clauses.append("lower(strategy_tag) = lower(%s)")
        params.append(strategy)
    if date_from:
        clauses.append("start_ts >= %s")
        params.append(date_from)
    if date_to:
        clauses.append("start_ts <= %s")
        params.append(date_to)
    where_sql = " and ".join(clauses)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                select run_id, mode, strategy_tag, start_ts::text, end_ts::text, initial_balance
                from runs
                where {where_sql}
                order by start_ts desc
                """,
                tuple(params),
            )
            runs = cur.fetchall()

            out = []
            for run_id, run_mode, strategy_tag, start_ts, end_ts, initial_balance in runs:
                cur.execute(
                    """
                    select symbol, entry_price, exit_price, qty, status, max_favorable_pnl_usdt, max_adverse_pnl_usdt
                    from legs
                    where run_id = %s
                    """,
                    (run_id,),
                )
                legs = cur.fetchall()

                # Final PnL (realized only)
                final_pnl = 0.0
                for _sym, entry, exit_price, qty, status, _max_fav, _max_adv in legs:
                    if status == "closed" and entry is not None and exit_price is not None and qty is not None:
                        final_pnl += (float(entry) - float(exit_price)) * float(qty)

                # Run max DD / peak PnL (aggregated unrealized)
                cur.execute(
                    """
                    select ts, sum(unrealized_pnl_usdt) as pnl
                    from snapshots
                    where run_id = %s
                    group by ts
                    """,
                    (run_id,),
                )
                series = cur.fetchall()
                max_dd = None
                peak_pnl = None
                if series:
                    pnls = [float(p[1] or 0) for p in series]
                    max_dd = min(pnls)
                    peak_pnl = max(pnls)

                # Close reason from latest run_completed event
                cur.execute(
                    """
                    select message
                    from events
                    where run_id = %s and type in ('paper_run_completed', 'live_run_completed')
                    order by ts desc
                    limit 1
                    """,
                    (run_id,),
                )
                row = cur.fetchone()
                close_reason = row[0] if row else None

                duration_hours = None
                if start_ts and end_ts:
                    try:
                        duration_hours = (
                            (_parse_dt(end_ts) - _parse_dt(start_ts)).total_seconds() / 3600.0
                        )
                    except Exception:
                        duration_hours = None

                out.append(
                    {
                        "run_id": run_id,
                        "mode": run_mode,
                        "strategy_tag": strategy_tag,
                        "start_ts": start_ts,
                        "end_ts": end_ts,
                        "duration_hours": duration_hours,
                        "close_reason": close_reason,
                        "initial_investment": float(initial_balance) if initial_balance is not None else None,
                        "final_pnl": final_pnl,
                        "max_dd": max_dd,
                        "peak_pnl": peak_pnl,
                    }
                )

    return {"runs": out}


@app.get("/reports/run")
def get_report_run(run_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select run_id, mode, strategy_tag, start_ts::text, end_ts::text, initial_balance
                from runs
                where run_id = %s
                """,
                (run_id,),
            )
            run = cur.fetchone()
            if not run:
                return {"run": None}

            cur.execute(
                """
                select symbol, entry_price, exit_price, qty, status, max_favorable_pnl_usdt, max_adverse_pnl_usdt
                from legs
                where run_id = %s
                order by symbol asc
                """,
                (run_id,),
            )
            legs = cur.fetchall()

            legs_out = []
            for sym, entry, exit_price, qty, status, max_fav, max_adv in legs:
                final_pnl = None
                if status == "closed" and entry is not None and exit_price is not None and qty is not None:
                    final_pnl = (float(entry) - float(exit_price)) * float(qty)
                legs_out.append(
                    {
                        "symbol": sym,
                        "status": status,
                        "entry_price": float(entry) if entry is not None else None,
                        "exit_price": float(exit_price) if exit_price is not None else None,
                        "qty": float(qty) if qty is not None else None,
                        "initial_investment": None,  # per-leg baseline is implicit by margin at open
                        "final_pnl": final_pnl,
                        "max_dd": float(max_adv) if max_adv is not None else None,
                        "peak_pnl": float(max_fav) if max_fav is not None else None,
                    }
                )

            # Run aggregated metrics
            cur.execute(
                """
                select ts, sum(unrealized_pnl_usdt) as pnl
                from snapshots
                where run_id = %s
                group by ts
                """,
                (run_id,),
            )
            series = cur.fetchall()
            max_dd = None
            peak_pnl = None
            if series:
                pnls = [float(p[1] or 0) for p in series]
                max_dd = min(pnls)
                peak_pnl = max(pnls)

            final_pnl = 0.0
            for l in legs_out:
                if l["final_pnl"] is not None:
                    final_pnl += l["final_pnl"]

            run_out = {
                "run_id": run[0],
                "mode": run[1],
                "strategy_tag": run[2],
                "start_ts": run[3],
                "end_ts": run[4],
                "initial_investment": float(run[5]) if run[5] is not None else None,
                "final_pnl": final_pnl,
                "max_dd": max_dd,
                "peak_pnl": peak_pnl,
            }
            return {"run": run_out, "legs": legs_out}


@app.get("/reports/aggregate")
def get_reports_aggregate(
    mode: str | None = None,
    strategy: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    runs = get_report_runs(mode=mode, strategy=strategy, date_from=date_from, date_to=date_to)["runs"]
    if not runs:
        return {"aggregate": None}

    # Convert to percent vs initial investment
    def pct(value: float | None, base: float | None) -> float | None:
        if value is None or base in (None, 0):
            return None
        return (value / base) * 100.0

    final_pnls = []
    max_dds = []
    peak_pnls = []
    for r in runs:
        base = r.get("initial_investment")
        final_pnls.append(pct(r.get("final_pnl"), base))
        max_dds.append(pct(r.get("max_dd"), base))
        peak_pnls.append(pct(r.get("peak_pnl"), base))

    # simple average, ignore None
    def avg(values: list[float | None]) -> float | None:
        nums = [v for v in values if v is not None]
        if not nums:
            return None
        return sum(nums) / len(nums)

    return {
        "aggregate": {
            "avg_final_pnl_pct": avg(final_pnls),
            "avg_max_dd_pct": avg(max_dds),
            "avg_peak_pnl_pct": avg(peak_pnls),
        }
    }


@app.get("/heartbeats/latest")
def get_latest_heartbeats(limit: int = 20):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select ts::text, service, status, message
                from heartbeats
                order by ts desc
                limit %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
            return {
                "heartbeats": [
                    {
                        "ts": r[0],
                        "service": r[1],
                        "status": r[2],
                        "message": r[3],
                    }
                    for r in rows
                ]
            }


@app.get("/events/latest")
def get_latest_events(limit: int = 50, run_id: str = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            if run_id:
                cur.execute(
                    """
                    select ts::text, level, type, message, run_id
                    from events
                    where run_id = %s
                    order by ts desc
                    limit %s
                    """,
                    (run_id, limit),
                )
            else:
                cur.execute(
                    """
                    select ts::text, level, type, message, run_id
                    from events
                    order by ts desc
                    limit %s
                    """,
                    (limit,),
                )
            rows = cur.fetchall()
            return {
                "events": [
                    {
                        "ts": r[0],
                        "level": r[1],
                        "type": r[2],
                        "message": r[3],
                        "run_id": r[4],
                    }
                    for r in rows
                ]
            }


@app.post("/commands/pause")
def command_pause():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into events (ts, level, type, message)
                values (now(), 'info', 'command_pause', 'pause requested')
                """
            )
        conn.commit()
    return {"ok": True}


@app.post("/commands/resume")
def command_resume():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into events (ts, level, type, message)
                values (now(), 'info', 'command_resume', 'resume requested')
                """
            )
        conn.commit()
    return {"ok": True}


@app.post("/commands/close_all")
def command_close_all():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into events (ts, level, type, message)
                values (now(), 'info', 'command_close_all', 'close all requested')
                """
            )
        conn.commit()
    return {"ok": True}


@app.post("/commands/set_global_tp")
def command_set_global_tp(payload: dict):
    percent = payload.get("percent")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into events (ts, level, type, message)
                values (now(), 'info', 'command_set_global_tp', %s)
                """,
                (f"set_global_tp {percent}",),
            )
        conn.commit()
    return {"ok": True}


@app.post("/commands/set_global_sl")
def command_set_global_sl(payload: dict):
    percent = payload.get("percent")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into events (ts, level, type, message)
                values (now(), 'info', 'command_set_global_sl', %s)
                """,
                (f"set_global_sl {percent}",),
            )
        conn.commit()
    return {"ok": True}


@app.post("/commands/leg_tp")
def command_leg_tp(payload: dict):
    symbol = payload.get("symbol")
    price = payload.get("price")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into events (ts, level, type, message)
                values (now(), 'info', 'command_leg_tp', %s)
                """,
                (f"{symbol} {price}",),
            )
        conn.commit()
    return {"ok": True}


@app.post("/commands/leg_sl")
def command_leg_sl(payload: dict):
    symbol = payload.get("symbol")
    price = payload.get("price")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into events (ts, level, type, message)
                values (now(), 'info', 'command_leg_sl', %s)
                """,
                (f"{symbol} {price}",),
            )
        conn.commit()
    return {"ok": True}


@app.post("/commands/leg_tp_clear")
def command_leg_tp_clear(payload: dict):
    symbol = payload.get("symbol")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into events (ts, level, type, message)
                values (now(), 'info', 'command_leg_tp_clear', %s)
                """,
                (f"{symbol}",),
            )
        conn.commit()
    return {"ok": True}


@app.post("/commands/leg_sl_clear")
def command_leg_sl_clear(payload: dict):
    symbol = payload.get("symbol")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into events (ts, level, type, message)
                values (now(), 'info', 'command_leg_sl_clear', %s)
                """,
                (f"{symbol}",),
            )
        conn.commit()
    return {"ok": True}
