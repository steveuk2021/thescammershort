import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.common.paper_trader import PaperTrader


if __name__ == "__main__":
    PaperTrader().run_once()
