from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .bitget_client import BitgetClient
from .bitget_symbols import filter_top_gainers
from .config import RuntimeSettings


@dataclass
class LegPlan:
    symbol: str
    change24h: float
    size: float
    margin_usdt: float
    leverage: float


@dataclass
class ExitDecision:
    exit: bool
    reason: Optional[str] = None


class StrategyEngine:
    def __init__(self, client: BitgetClient, settings: RuntimeSettings) -> None:
        self.client = client
        self.settings = settings

    def select_top_gainers_from_tickers(self, tickers: Dict[str, Any], top_n: int) -> List[Dict[str, Any]]:
        return filter_top_gainers(tickers, top_n=top_n)

    def select_top_gainers(self, top_n: int) -> List[Dict[str, Any]]:
        tickers = self.client.get_usdt_perp_tickers()
        return self.select_top_gainers_from_tickers(tickers, top_n=top_n)

    def apply_max_pump_filter(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for item in items:
            try:
                change = float(item.get("change24h", 0))
            except Exception:
                change = 0.0
            if change >= self.settings.max_pump_pct:
                out.append(item)
        return out

    def get_contract_specs(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        specs: Dict[str, Dict[str, float]] = {}
        resp = self.client.get_contracts()
        for item in resp.get("data", []):
            sym = item.get("symbol")
            if sym in symbols:
                specs[sym] = {
                    "minTradeNum": float(item.get("minTradeNum", 0)),
                    "sizeMultiplier": float(item.get("sizeMultiplier", 1)),
                }
        return specs

    def compute_size(self, symbol: str, last_price: float, specs: Dict[str, Dict[str, float]]) -> float:
        # notional = margin * leverage
        notional = self.settings.margin_per_leg_usdt * self.settings.leverage
        # size in contracts = notional / price
        raw_size = notional / last_price if last_price > 0 else 0.0

        spec = specs.get(symbol, {"minTradeNum": 0.0, "sizeMultiplier": 1.0})
        step = spec["sizeMultiplier"]
        min_size = spec["minTradeNum"]

        # round down to step
        if step > 0:
            size = (raw_size // step) * step
        else:
            size = raw_size

        # enforce minimum size
        if size < min_size:
            size = 0.0
        return float(size)

    def build_leg_plan_from_tickers(self, tickers: Dict[str, Any]) -> List[LegPlan]:
        # 1) filter full universe by max pump
        universe = tickers.get("data", []) if isinstance(tickers, dict) else []
        universe = self.apply_max_pump_filter(universe)
        # 2) select top gainers from filtered universe
        candidates = self.select_top_gainers_from_tickers({"data": universe}, self.settings.num_legs)

        symbols = [c.get("symbol") for c in candidates if c.get("symbol")]
        specs = self.get_contract_specs(symbols)

        legs: List[LegPlan] = []
        for item in candidates:
            symbol = item.get("symbol")
            if not symbol:
                continue
            last_price = float(item.get("lastPr", 0) or 0)
            size = self.compute_size(symbol, last_price, specs)
            if size <= 0:
                continue
            legs.append(
                LegPlan(
                    symbol=symbol,
                    change24h=float(item.get("change24h", 0)),
                    size=size,
                    margin_usdt=self.settings.margin_per_leg_usdt,
                    leverage=self.settings.leverage,
                )
            )
        return legs

    def build_leg_plan(self) -> List[LegPlan]:
        tickers = self.client.get_usdt_perp_tickers()
        return self.build_leg_plan_from_tickers(tickers)

    def evaluate_leg_exit(
        self,
        leg_pnl_pct: float,
        max_leg_pnl_pct: float,
        strategy_tag: str,
    ) -> ExitDecision:
        # leg_pnl_pct is measured against per-leg margin (e.g. +1.0 = +100%)
        if strategy_tag == "s3":
            # trailing stop after +100%: 5% retracement from max
            if max_leg_pnl_pct >= 1.0 and leg_pnl_pct <= max_leg_pnl_pct - 0.05:
                return ExitDecision(True, "leg_trailing_sl")
        return ExitDecision(False, None)

    def evaluate_portfolio_exit(
        self,
        portfolio_pnl_pct: float,
        hours_elapsed: float,
        strategy_tag: str,
    ) -> ExitDecision:
        # portfolio_pnl_pct is measured against total margin at risk
        if strategy_tag != "s2" and portfolio_pnl_pct <= -self.settings.global_kill_dd_pct:
            return ExitDecision(True, "kill_switch")

        if hours_elapsed >= 24.0:
            return ExitDecision(True, "24h")

        if strategy_tag in ("s1", "s3"):
            if portfolio_pnl_pct >= 0.30:
                return ExitDecision(True, "portfolio_tp")
            if portfolio_pnl_pct <= -0.30:
                return ExitDecision(True, "portfolio_sl")

        return ExitDecision(False, None)
