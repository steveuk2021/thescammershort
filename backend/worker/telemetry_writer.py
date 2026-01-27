from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.common.db import get_conn


def write_heartbeat(service: str = "worker") -> None:
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into heartbeats (ts, service, status, message)
                values (%s, %s, %s, %s)
                """,
                (now, service, "ok", "heartbeat"),
            )
        conn.commit()


def write_snapshot(run_id: str, exchange: str, symbol: str, price: float, pnl: float) -> None:
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into snapshots (ts, run_id, exchange, symbol, price, unrealized_pnl_usdt)
                values (%s, %s, %s, %s, %s, %s)
                """,
                (now, run_id, exchange, symbol, price, pnl),
            )
        conn.commit()


if __name__ == "__main__":
    # Minimal manual test
    write_heartbeat("worker")
    print("Heartbeat written")
