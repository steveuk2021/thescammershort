from backend.common.bitget_client import BitgetClient
from backend.common.strategy import StrategyEngine


def main() -> None:
    client = BitgetClient()
    engine = StrategyEngine(client)
    legs = engine.build_leg_plan()

    print("Legs selected:", len(legs))
    for leg in legs:
        print(leg)


if __name__ == "__main__":
    main()
