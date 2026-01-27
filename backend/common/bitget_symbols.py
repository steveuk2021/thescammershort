from typing import Any


def filter_top_gainers(tickers_resp: Any, top_n: int = 10) -> list[dict[str, Any]]:
    # Bitget mix tickers returns list under data
    data = tickers_resp.get("data", []) if isinstance(tickers_resp, dict) else []

    def pct_change(item: dict[str, Any]) -> float:
        try:
            # v2 tickers use change24h
            val = item.get("change24h")
            if val is None:
                val = item.get("change")
            if val is None:
                val = item.get("chg")
            return float(val)
        except Exception:
            return 0.0

    # Sort by 24h % change desc
    sorted_items = sorted(data, key=pct_change, reverse=True)
    return sorted_items[:top_n]
