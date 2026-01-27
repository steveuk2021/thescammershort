import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.common.live_trader import LiveTrader


if __name__ == "__main__":
    LiveTrader().run_forever()
