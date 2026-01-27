from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.common.db import get_conn


def main() -> None:
    now = datetime.now(timezone.utc)
    test_run_id = "00000000-0000-0000-0000-000000000000"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into runs (run_id, exchange, mode, entry_time_utc, start_ts, status, num_legs,
                                  margin_per_leg_usdt, leverage, max_pump_pct, global_kill_dd_pct)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                on conflict (run_id) do nothing
                """,
                (
                    test_run_id,
                    "bitget",
                    "paper",
                    "04:00",
                    now,
                    "running",
                    10,
                    100,
                    3,
                    0.15,
                    0.30,
                ),
            )

            cur.execute(
                """
                insert into snapshots (ts, run_id, exchange, symbol, price, unrealized_pnl_usdt)
                values (%s, %s, %s, %s, %s, %s)
                """,
                (now, test_run_id, "bitget", "BTCUSDT", 50000.0, -12.34),
            )

            cur.execute(
                """
                insert into heartbeats (ts, service, status, message)
                values (%s, %s, %s, %s)
                """,
                (now, "worker", "ok", "test heartbeat"),
            )
        conn.commit()

    print("Inserted test run + snapshot + heartbeat")


if __name__ == "__main__":
    main()
