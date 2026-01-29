import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from .bitget_client import BitgetClient
from .config import settings, live_settings
from .strategy import StrategyEngine
from .db import get_conn
from backend.worker.telemetry_writer import write_heartbeat
from .db_ops import (
    create_run,
    end_run,
    get_active_run,
    get_open_legs,
    get_run_balances,
    get_settings,
    insert_event,
    insert_leg,
    insert_order,
    insert_snapshot,
    upsert_live_leg,
    update_leg_exit,
    update_leg_max,
    update_run_status,
    update_run_balance,
)
from .run_window import within_entry_window


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LiveTrader:
    def __init__(self) -> None:
        self.settings = live_settings
        self.client = BitgetClient()
        self.engine = StrategyEngine(self.client, self.settings)
        self.run_id: str | None = None
        self.legs: Dict[str, Dict[str, float]] = {}
        self.max_leg_pnl_pct: Dict[str, float] = {}
        self.initial_balance: float | None = None

    def _select_and_open(self) -> None:
        if self.settings.status != "on":
            print("[live] LIVE_STATUS is off; exiting")
            return
        # Resume active live run if exists
        active = get_active_run(mode="live")
        if active:
            self.run_id = active.run_id
            initial, current = get_run_balances(self.run_id)
            if initial is None:
                initial = self.settings.initial_balance
                if initial is None:
                    insert_event("error", "live_initial_balance_required", "LIVE_INITIAL_BALANCE is required for live runs", self.run_id)
                    print("[live] LIVE_INITIAL_BALANCE is required; exiting")
                    return
                update_run_balance(self.run_id, initial_balance=initial, current_balance=current or initial)
            self.initial_balance = initial
            for sym, entry, qty in get_open_legs(self.run_id):
                self.legs[sym] = {"entry": float(entry), "qty": float(qty)}
                self.max_leg_pnl_pct[sym] = 0.0
            print(f"[live] resumed run {self.run_id} legs={len(self.legs)}")
            return

        if not within_entry_window(self.settings.entry_time_utc, window_minutes=60):
            print("[live] outside entry window; waiting for next cycle")
            return

        legs = self.engine.build_leg_plan()
        if not legs:
            insert_event("warn", "live_no_legs", "no legs selected", None)
            print("[live] no legs selected")
            return

        self.run_id = str(uuid.uuid4())
        self.initial_balance = self.settings.initial_balance
        if self.initial_balance is None:
            insert_event("error", "live_initial_balance_required", "LIVE_INITIAL_BALANCE is required for live runs", None)
            print("[live] LIVE_INITIAL_BALANCE is required; exiting")
            self.run_id = None
            return
        create_run(
            run_id=self.run_id,
            exchange=self.settings.exchange,
            mode=self.settings.mode,
            entry_time_utc=self.settings.entry_time_utc,
            num_legs=self.settings.num_legs,
            margin_per_leg_usdt=self.settings.margin_per_leg_usdt,
            leverage=self.settings.leverage,
            max_pump_pct=self.settings.max_pump_pct,
            global_kill_dd_pct=self.settings.global_kill_dd_pct,
            strategy_tag=self.settings.strategy_tag,
            initial_balance=self.initial_balance,
            current_balance=self.initial_balance,
        )

        for leg in legs:
            # Ensure exchange leverage matches config before opening
            leverage_str = f"{self.settings.leverage:g}"
            lev_resp = self.client.set_leverage(
                leg.symbol,
                leverage_str,
                hold_side=settings.bitget_hold_side or None,
            )
            if lev_resp.get("code") != "00000":
                msg = f"set_leverage failed {leg.symbol} code={lev_resp.get('code')} msg={lev_resp.get('msg')}"
                insert_event("warn", "live_set_leverage_failed", msg, self.run_id)
                print(f"[live] {msg}")

            entry_price = self._get_mark_price(leg.symbol)
            self.legs[leg.symbol] = {"entry": entry_price, "qty": leg.size}
            self.max_leg_pnl_pct[leg.symbol] = 0.0

            # Place live order: open short
            resp = self.client.place_order(
                symbol=leg.symbol,
                side="sell",
                size=str(leg.size),
                trade_side="open",
                reduce_only="NO",
            )
            insert_leg(
                run_id=self.run_id,
                symbol=leg.symbol,
                entry_price=entry_price,
                qty=leg.size,
            )
            insert_order(
                run_id=self.run_id,
                symbol=leg.symbol,
                side="sell",
                action="open",
                intent_price=entry_price,
                fill_price=entry_price,
                qty=leg.size,
                status="filled" if resp.get("code") == "00000" else "submitted",
            )
            print(f"[live] opened {leg.symbol} @ {entry_price} qty={leg.size}")

        insert_event("info", "live_run_started", "live run started", self.run_id)
        print(f"[live] run started {self.run_id} legs={len(legs)}")

    def _get_mark_price(self, symbol: str) -> float:
        tickers = self.client.get_usdt_perp_tickers().get("data", [])
        for t in tickers:
            if t.get("symbol") == symbol:
                return float(t.get("markPrice") or t.get("lastPr") or 0)
        return 0.0

    def _get_account_equity(self) -> float:
        resp = self.client.get_accounts()
        for item in resp.get("data", []):
            if item.get("marginCoin") == "USDT":
                return float(item.get("accountEquity") or item.get("usdtEquity") or 0)
        return 0.0

    def _poll_and_update(self) -> None:
        if not self.run_id:
            return

        poll_start = _now()
        # Pull positions from exchange
        positions = self.client.get_positions().get("data", [])
        live_positions = [
            p
            for p in positions
            if p.get("symbol") and (p.get("holdSide") == "short" or p.get("holdSide") is None)
        ]
        pos_by_symbol = {p.get("symbol"): p for p in live_positions if p.get("symbol")}

        poll_ts = _now()
        leg_upsert_rows = []
        snapshots_rows = []
        leg_max_rows = []
        leg_exit_rows = []
        order_rows = []
        event_rows = []

        # Reconcile: if DB thinks open but exchange shows closed, mark closed
        for sym in list(self.legs.keys()):
            if sym not in pos_by_symbol:
                mark = self._get_mark_price(sym)
                leg_exit_rows.append((mark, poll_ts, "manual", self.run_id, sym))
                event_rows.append((poll_ts, "info", "live_leg_closed_manual", f"{sym} closed on exchange", self.run_id))
                self.legs.pop(sym, None)
                self.max_leg_pnl_pct.pop(sym, None)

        portfolio_pnl = 0.0
        for sym, pos in pos_by_symbol.items():
            entry = float(pos.get("openPriceAvg") or 0)
            qty = float(pos.get("total") or 0)
            margin = float(pos.get("marginSize") or 0)
            leverage = float(pos.get("leverage") or 0)
            mark = float(pos.get("markPrice") or 0)
            pnl = float(pos.get("unrealizedPL") or 0)

            # Sync DB leg with live exchange state
            leg_upsert_rows.append((self.run_id, sym, entry, qty))
            self.legs[sym] = {"entry": entry, "qty": qty}
            if sym not in self.max_leg_pnl_pct:
                self.max_leg_pnl_pct[sym] = 0.0

            snapshots_rows.append(
                (
                    poll_ts,
                    self.run_id,
                    self.settings.exchange,
                    sym,
                    mark,
                    pnl,
                    entry,
                    qty,
                    margin,
                    leverage,
                )
            )
            leg_max_rows.append((pnl, pnl, self.run_id, sym))

            margin_basis = margin if margin > 0 else self.settings.margin_per_leg_usdt
            pnl_pct = pnl / margin_basis
            if pnl_pct > self.max_leg_pnl_pct.get(sym, 0.0):
                self.max_leg_pnl_pct[sym] = pnl_pct

            leg_decision = self.engine.evaluate_leg_exit(
                leg_pnl_pct=pnl_pct,
                max_leg_pnl_pct=self.max_leg_pnl_pct.get(sym, 0.0),
                strategy_tag=self.settings.strategy_tag.lower(),
            )
            if leg_decision.exit:
                self.client.close_position_market(sym, str(qty), position_side="short")
                reason = leg_decision.reason or "leg_trailing_sl"
                leg_exit_rows.append((mark, poll_ts, reason, self.run_id, sym))
                order_rows.append(
                    (
                        self.run_id,
                        sym,
                        "buy",
                        "close",
                        mark,
                        mark,
                        qty,
                        "submitted",
                        poll_ts,
                    )
                )
                event_rows.append((poll_ts, "info", "live_leg_closed", f"{sym} {reason}", self.run_id))
                self.legs.pop(sym, None)
                self.max_leg_pnl_pct.pop(sym, None)
                continue

            portfolio_pnl += pnl

        if self.run_id:
            update_run_balance(self.run_id, current_balance=self._get_account_equity())

        if leg_upsert_rows or snapshots_rows or leg_max_rows or leg_exit_rows or order_rows or event_rows:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    if leg_upsert_rows:
                        cur.executemany(
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
                            [(r[0], r[1], r[2], poll_ts, r[3]) for r in leg_upsert_rows],
                        )
                    if snapshots_rows:
                        cur.executemany(
                            """
                            insert into snapshots (
                                ts, run_id, exchange, symbol, price, unrealized_pnl_usdt,
                                entry_price, position_size, margin_usdt, leverage
                            )
                            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            snapshots_rows,
                        )
                    if leg_max_rows:
                        cur.executemany(
                            """
                            update legs
                            set max_favorable_pnl_usdt = greatest(max_favorable_pnl_usdt, %s),
                                max_adverse_pnl_usdt = least(max_adverse_pnl_usdt, %s)
                            where run_id = %s and symbol = %s
                            """,
                            leg_max_rows,
                        )
                    if leg_exit_rows:
                        cur.executemany(
                            """
                            update legs
                            set exit_price = %s, exit_ts = %s, exit_reason = %s, status = 'closed'
                            where run_id = %s and symbol = %s
                            """,
                            leg_exit_rows,
                        )
                    if order_rows:
                        cur.executemany(
                            """
                            insert into orders (run_id, symbol, side, action, intent_price, fill_price, qty, status, ts)
                            values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            order_rows,
                        )
                    if event_rows:
                        cur.executemany(
                            """
                            insert into events (ts, level, type, message, run_id)
                            values (%s, %s, %s, %s, %s)
                            """,
                            event_rows,
                        )
                conn.commit()
        poll_end = _now()
        print(
            "[live] poll timing",
            f"positions={(poll_ts - poll_start).total_seconds():.2f}s",
            f"db={(poll_end - poll_ts).total_seconds():.2f}s",
            f"total={(poll_end - poll_start).total_seconds():.2f}s",
        )

        # Skip exit if paused
        active = get_active_run(mode="live")
        if active and active.run_id == self.run_id and active.status == "paused":
            return

        hours_elapsed = 0.0
        if active and active.start_ts:
            try:
                start_ts = datetime.fromisoformat(active.start_ts)
                hours_elapsed = (_now() - start_ts).total_seconds() / 3600
            except Exception:
                hours_elapsed = 0.0

        leg_count = len(pos_by_symbol)
        if leg_count > 0:
            margin_total = self.settings.margin_per_leg_usdt * leg_count
            portfolio_pnl_pct = portfolio_pnl / margin_total
        else:
            portfolio_pnl_pct = 0.0
        decision = self.engine.evaluate_portfolio_exit(
            portfolio_pnl_pct,
            hours_elapsed,
            self.settings.strategy_tag.lower(),
        )
        if decision.exit:
            for sym in list(self.legs.keys()):
                mark = self._get_mark_price(sym)
                self.client.close_position_market(sym, str(self.legs[sym]["qty"]), position_side="short")
                update_leg_exit(self.run_id, sym, mark, decision.reason or "24h")
                insert_order(
                    run_id=self.run_id,
                    symbol=sym,
                    side="buy",
                    action="close",
                    intent_price=mark,
                    fill_price=mark,
                    qty=self.legs[sym]["qty"],
                    status="submitted",
                )
                print(f"[live] closed {sym} reason={decision.reason}")
            update_run_status(self.run_id, "completed")
            end_run(self.run_id)
            insert_event("info", "live_run_completed", f"exit {decision.reason}", self.run_id)
            print(f"[live] run completed reason={decision.reason}")
            # Prevent duplicate close and allow new run within the same entry window
            self.legs.clear()
            self.max_leg_pnl_pct.clear()
            self.run_id = None
            return

    def run_forever(self) -> None:
        while True:
            write_heartbeat("live")
            self._refresh_settings()
            if not self.run_id:
                self._select_and_open()
            print(f"[live] poll tick {datetime.now(timezone.utc).isoformat()} interval={self.settings.poll_interval_sec}s")
            if self.run_id:
                self._poll_and_update()
            time.sleep(self.settings.poll_interval_sec)

    def _refresh_settings(self) -> None:
        try:
            overrides = get_settings(self.settings.mode)
            if overrides:
                self.settings.apply_overrides(overrides)
        except Exception:
            return
