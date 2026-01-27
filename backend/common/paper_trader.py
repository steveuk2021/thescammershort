import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from .bitget_client import BitgetClient
from .config import settings, paper_settings
from .strategy import StrategyEngine
from .db import get_conn
from backend.worker.telemetry_writer import write_heartbeat
from .db_ops import (
    create_run,
    end_run,
    get_active_run,
    get_legs,
    get_run_balances,
    insert_event,
    insert_leg,
    insert_order,
    insert_snapshot,
    get_open_legs,
    update_leg_exit,
    update_leg_max,
    update_run_status,
    update_run_balance,
)
from .run_window import within_entry_window


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _pnl_usdt_short(entry_price: float, mark_price: float, qty: float) -> float:
    return (entry_price - mark_price) * qty


class PaperTrader:
    def __init__(self) -> None:
        self.settings = paper_settings
        self.client = BitgetClient()
        self.engine = StrategyEngine(self.client, self.settings)
        self.run_id: str | None = None
        self.legs: Dict[str, Dict[str, float]] = {}
        self.max_leg_pnl_pct: Dict[str, float] = {}
        self.initial_balance: float | None = None
        self.realized_pnl: float = 0.0

    def _select_and_open(self) -> None:
        if self.settings.status != "on":
            print("[paper] PAPER_STATUS is off; exiting")
            return
        # Resume active paper run if exists
        active = get_active_run(mode="paper")
        if active:
            self.run_id = active.run_id
            initial, current = get_run_balances(self.run_id)
            if initial is None:
                initial = self.settings.initial_balance
                update_run_balance(self.run_id, initial_balance=initial, current_balance=current or initial)
            self.initial_balance = initial
            self.realized_pnl = 0.0
            for sym, entry, exit_price, qty, status, _exit_ts in get_legs(self.run_id):
                if status == "closed" and entry is not None and exit_price is not None and qty is not None:
                    self.realized_pnl += _pnl_usdt_short(float(entry), float(exit_price), float(qty))
            for sym, entry, qty in get_open_legs(self.run_id):
                self.legs[sym] = {"entry": float(entry), "qty": float(qty)}
                self.max_leg_pnl_pct[sym] = 0.0
            print(f"[paper] resumed run {self.run_id} legs={len(self.legs)}")
            return

        if not within_entry_window(self.settings.entry_time_utc, window_minutes=60):
            print("[paper] outside entry window; waiting for next cycle")
            return

        legs = self.engine.build_leg_plan()
        if not legs:
            insert_event("warn", "paper_no_legs", "no legs selected", None)
            print("[paper] no legs selected")
            return

        self.run_id = str(uuid.uuid4())
        self.initial_balance = self.settings.initial_balance
        self.realized_pnl = 0.0
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

        # Fetch tickers once to avoid repeated API calls per leg
        tickers = {t.get("symbol"): t for t in self.client.get_usdt_perp_tickers().get("data", [])}
        for leg in legs:
            # entry price from latest tickers
            entry_price = float(
                (tickers.get(leg.symbol, {}) or {}).get("markPrice")
                or (tickers.get(leg.symbol, {}) or {}).get("lastPr")
                or 0
            )
            self.legs[leg.symbol] = {"entry": entry_price, "qty": leg.size}
            self.max_leg_pnl_pct[leg.symbol] = 0.0
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
                status="filled",
            )
            print(f"[paper] opened {leg.symbol} @ {entry_price} qty={leg.size}")

        insert_event("info", "paper_run_started", "paper run started", self.run_id)
        print(f"[paper] run started {self.run_id} legs={len(legs)}")

    def _get_mark_price(self, symbol: str) -> float:
        tickers = self.client.get_usdt_perp_tickers().get("data", [])
        for t in tickers:
            if t.get("symbol") == symbol:
                return float(t.get("markPrice") or t.get("lastPr") or 0)
        return 0.0

    def _poll_and_update(self) -> None:
        if not self.run_id:
            return

        poll_start = _now()
        # Pull latest tickers once
        tickers_resp = self.client.get_usdt_perp_tickers()
        tickers = {t.get("symbol"): t for t in tickers_resp.get("data", [])}
        tickers_done = _now()

        poll_ts = _now()
        snapshots_rows = []
        leg_max_rows = []
        leg_exit_rows = []
        order_rows = []
        event_rows = []

        portfolio_pnl = 0.0
        open_symbols: List[str] = list(self.legs.keys())
        for sym in open_symbols:
            t = tickers.get(sym, {})
            mark = float(t.get("markPrice") or t.get("lastPr") or 0)
            entry = self.legs[sym]["entry"]
            qty = self.legs[sym]["qty"]
            if mark <= 0:
                continue

            # snapshot and pnl
            pnl = _pnl_usdt_short(entry, mark, qty=qty)
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
                    self.settings.margin_per_leg_usdt,
                    self.settings.leverage,
                )
            )
            leg_max_rows.append((pnl, pnl, self.run_id, sym))
            pnl_pct = pnl / self.settings.margin_per_leg_usdt
            if pnl_pct > self.max_leg_pnl_pct.get(sym, 0.0):
                self.max_leg_pnl_pct[sym] = pnl_pct

            # leg-level exit (S3 trailing)
            leg_decision = self.engine.evaluate_leg_exit(
                leg_pnl_pct=pnl_pct,
                max_leg_pnl_pct=self.max_leg_pnl_pct.get(sym, 0.0),
                strategy_tag=self.settings.strategy_tag.lower(),
            )
            if leg_decision.exit:
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
                        "filled",
                        poll_ts,
                    )
                )
                self.realized_pnl += _pnl_usdt_short(entry, mark, qty=qty)
                event_rows.append((poll_ts, "info", "paper_leg_closed", f"{sym} {reason}", self.run_id))
                print(f"[paper] closed {sym} reason={leg_decision.reason}")
                self.legs.pop(sym, None)
                self.max_leg_pnl_pct.pop(sym, None)
                continue

            portfolio_pnl += pnl

        # Evaluate exit
        latest = get_active_run(mode="paper")
        if latest and latest.run_id == self.run_id and latest.status == "paused":
            return

        hours_elapsed = 0.0
        if latest and latest.start_ts:
            try:
                start_ts = datetime.fromisoformat(latest.start_ts)
                hours_elapsed = ( _now() - start_ts ).total_seconds() / 3600
            except Exception:
                hours_elapsed = 0.0

        if snapshots_rows or leg_max_rows or leg_exit_rows or order_rows or event_rows:
            with get_conn() as conn:
                with conn.cursor() as cur:
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

        portfolio_pnl_pct = portfolio_pnl / (self.settings.margin_per_leg_usdt * self.settings.num_legs)
        decision = self.engine.evaluate_portfolio_exit(
            portfolio_pnl_pct,
            hours_elapsed,
            self.settings.strategy_tag.lower(),
        )
        if self.run_id:
            base_balance = self.initial_balance if self.initial_balance is not None else self.settings.initial_balance
            update_run_balance(self.run_id, current_balance=base_balance + self.realized_pnl + portfolio_pnl)
        if decision.exit:
            # Close all legs
            for sym in list(self.legs.keys()):
                entry = self.legs[sym]["entry"]
                mark = self._get_mark_price(sym)
                self.realized_pnl += _pnl_usdt_short(entry, mark, qty=self.legs[sym]["qty"])
                update_leg_exit(self.run_id, sym, mark, decision.reason or "24h")
                insert_order(
                    run_id=self.run_id,
                    symbol=sym,
                    side="buy",
                    action="close",
                    intent_price=mark,
                    fill_price=mark,
                    qty=self.legs[sym]["qty"],
                    status="filled",
                )
                print(f"[paper] closed {sym} reason={decision.reason}")
            update_run_status(self.run_id, "completed")
            end_run(self.run_id)
            insert_event("info", "paper_run_completed", f"exit {decision.reason}", self.run_id)
            print(f"[paper] run completed reason={decision.reason}")
            # Prevent duplicate close on next tick
            self.legs.clear()
            self.max_leg_pnl_pct.clear()
            self.run_id = None
            return

        poll_end = _now()
        print(
            "[paper] poll timing",
            f"tickers={(tickers_done - poll_start).total_seconds():.2f}s",
            f"total={(poll_end - poll_start).total_seconds():.2f}s",
        )

    def run_once(self) -> None:
        self._select_and_open()
        while True:
            write_heartbeat("paper")
            print(f"[paper] poll tick {datetime.now(timezone.utc).isoformat()} interval={self.settings.poll_interval_sec}s")
            self._poll_and_update()
            time.sleep(self.settings.poll_interval_sec)
