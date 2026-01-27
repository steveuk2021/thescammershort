import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.common.bitget_client import BitgetClient
from backend.common.strategy import StrategyEngine


def main() -> None:
    sample_path = Path("sample_output.json")
    if not sample_path.exists():
        raise SystemExit("sample_output.json not found. Run scripts_dump_tickers.py first.")

    with sample_path.open("r", encoding="utf-8") as f:
        tickers = json.load(f)

    engine = StrategyEngine(BitgetClient())
    legs = engine.build_leg_plan_from_tickers(tickers)

    print("Legs selected:", len(legs))
    for leg in legs:
        print(leg)


if __name__ == "__main__":
    main()
