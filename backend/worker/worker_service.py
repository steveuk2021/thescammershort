import time
import uuid
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.common.config import live_settings, paper_settings
from backend.common.db_ops import (
    create_run,
    get_active_run,
    get_latest_command,
    get_latest_run,
    insert_event,
    update_run_status,
)
from backend.common.time_utils import now_utc, parse_entry_time_utc
from backend.worker.telemetry_writer import write_heartbeat


class WorkerService:
    def __init__(self) -> None:
        self.last_command_ts = None

    def _should_run_today(self, trade_weekends: bool) -> bool:
        if trade_weekends:
            return True
        # Monday = 0, Sunday = 6
        return now_utc().weekday() < 5

    def _entry_time_reached(self, entry_time_utc: str) -> bool:
        entry_time = parse_entry_time_utc(entry_time_utc)
        now = now_utc()
        today_entry = datetime.combine(now.date(), entry_time)
        return now >= today_entry

    def _run_exists_today(self, mode: str) -> bool:
        latest = get_latest_run(mode=mode)
        if not latest:
            return False
        try:
            last_start = datetime.fromisoformat(latest.start_ts)
        except Exception:
            return False
        return last_start.date() == now_utc().date()

    def _handle_command(self, run_ids: list[str]) -> None:
        cmd = get_latest_command(self.last_command_ts)
        if not cmd:
            return
        cmd_type, message = cmd
        # track last command time as now (simple ack)
        self.last_command_ts = datetime.now(timezone.utc).isoformat()

        for run_id in run_ids:
            if cmd_type == "command_pause":
                update_run_status(run_id, "paused")
                insert_event("info", "command_ack", f"paused: {message}", run_id)
            elif cmd_type == "command_resume":
                update_run_status(run_id, "running")
                insert_event("info", "command_ack", f"resumed: {message}", run_id)
            elif cmd_type == "command_close_all":
                update_run_status(run_id, "stopped")
                insert_event("info", "command_ack", f"close_all: {message}", run_id)

    def tick(self) -> None:
        now = now_utc()
        print(f"[worker] tick {now.isoformat()}")
        write_heartbeat("worker")

        active_by_mode: dict[str, str] = {}
        for mode in ("paper", "live"):
            active = get_active_run(mode=mode)
            if active and active.status in ("running", "paused") and active.end_ts is None:
                print(f"[worker] active {mode} run {active.run_id} status={active.status}")
                active_by_mode[mode] = active.run_id

        if active_by_mode:
            self._handle_command(list(active_by_mode.values()))

        for mode, runtime in (("paper", paper_settings), ("live", live_settings)):
            if runtime.status != "on":
                continue
            if mode in active_by_mode:
                continue

            # check schedule per mode
            if not self._should_run_today(runtime.trade_weekends):
                print(f"[worker] skip {mode}: weekend disabled")
                continue
            if not self._entry_time_reached(runtime.entry_time_utc):
                print(f"[worker] skip {mode}: entry time not reached")
                continue
            if self._run_exists_today(mode):
                print(f"[worker] skip {mode}: run already exists today")
                continue

            run_id = str(uuid.uuid4())
            create_run(
                run_id=run_id,
                exchange=runtime.exchange,
                mode=runtime.mode,
                entry_time_utc=runtime.entry_time_utc,
                num_legs=runtime.num_legs,
                margin_per_leg_usdt=runtime.margin_per_leg_usdt,
                leverage=runtime.leverage,
                max_pump_pct=runtime.max_pump_pct,
                global_kill_dd_pct=runtime.global_kill_dd_pct,
                strategy_tag=runtime.strategy_tag,
            )
            insert_event("info", "run_started", f"{mode} run created", run_id)
            print(f"[worker] {mode} run created {run_id}")

    def run_forever(self) -> None:
        while True:
            self.tick()
            time.sleep(5)


if __name__ == "__main__":
    WorkerService().run_forever()
