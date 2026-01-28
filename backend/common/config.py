import os
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


def getenv(key: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(key, default)
    return value


class GlobalSettings:
    def __init__(self) -> None:
        self.app_env = getenv("APP_ENV", "local")
        self.exchange = getenv("EXCHANGE", "bitget")
        self.use_testnet = getenv("USE_TESTNET", "true").lower() == "true"
        self.paper_status = getenv("PAPER_STATUS", "on").lower()
        self.live_status = getenv("LIVE_STATUS", "off").lower()
        self.paper_mode = "paper"
        self.live_mode = "live"
        self.mode = "paper"

        # Base defaults
        self.entry_time_utc = getenv("ENTRY_TIME_UTC", "04:00")
        self.trade_weekends = getenv("TRADE_WEEKENDS", "true").lower() == "true"
        self.num_legs = int(getenv("NUM_LEGS", "10"))
        self.margin_per_leg_usdt = float(getenv("MARGIN_PER_LEG_USDT", "100"))
        self.leverage = float(getenv("LEVERAGE", "3"))
        self.max_pump_pct = float(getenv("MAX_PUMP_PCT", "0.15"))
        self.global_kill_dd_pct = float(getenv("GLOBAL_KILL_DD_PCT", "0.30"))
        self.poll_interval_sec = int(getenv("POLL_INTERVAL_SEC", "30"))
        self.strategy_tag = getenv("STRATEGY_TAG", "S1")
        self.paper_initial_balance = float(getenv("PAPER_INITIAL_BALANCE", "1000"))
        self.hold_hours = float(getenv("HOLD_HOURS", "24"))

        # Secrets / infra
        self.bitget_api_key = getenv("BITGET_API_KEY", "")
        self.bitget_api_secret = getenv("BITGET_API_SECRET", "")
        self.bitget_api_passphrase = getenv("BITGET_API_PASSPHRASE", "")
        self.bitget_base_url = getenv("BITGET_BASE_URL", "https://api.bitget.com")
        self.bitget_hold_side = getenv("BITGET_HOLD_SIDE", "")

        self.database_url = getenv("DATABASE_URL", "")
        self.api_port = int(getenv("API_PORT", "8000"))
        self.worker_heartbeat_sec = int(getenv("WORKER_HEARTBEAT_SEC", "60"))


class RuntimeSettings:
    def __init__(self, prefix: str, mode: str, base: GlobalSettings) -> None:
        self.mode = mode
        self.status = getenv(f"{prefix}_STATUS", "on" if prefix == "PAPER" else "off").lower()
        self.exchange = base.exchange
        self.entry_time_utc = getenv(f"{prefix}_ENTRY_TIME_UTC", base.entry_time_utc)
        self.trade_weekends = getenv(f"{prefix}_TRADE_WEEKENDS", str(base.trade_weekends)).lower() == "true"
        self.num_legs = int(getenv(f"{prefix}_NUM_LEGS", str(base.num_legs)))
        self.margin_per_leg_usdt = float(getenv(f"{prefix}_MARGIN_PER_LEG_USDT", str(base.margin_per_leg_usdt)))
        self.leverage = float(getenv(f"{prefix}_LEVERAGE", str(base.leverage)))
        self.max_pump_pct = float(getenv(f"{prefix}_MAX_PUMP_PCT", str(base.max_pump_pct)))
        self.global_kill_dd_pct = float(getenv(f"{prefix}_GLOBAL_KILL_DD_PCT", str(base.global_kill_dd_pct)))
        self.poll_interval_sec = int(getenv(f"{prefix}_POLL_INTERVAL_SEC", str(base.poll_interval_sec)))
        self.strategy_tag = getenv(f"{prefix}_STRATEGY_TAG", base.strategy_tag)
        self.hold_hours = float(getenv(f"{prefix}_HOLD_HOURS", str(base.hold_hours)))
        initial_balance_env = os.getenv(f"{prefix}_INITIAL_BALANCE")
        if initial_balance_env is not None and initial_balance_env != "":
            self.initial_balance = float(initial_balance_env)
        elif prefix == "PAPER":
            self.initial_balance = base.paper_initial_balance
        else:
            self.initial_balance = None


settings = GlobalSettings()
paper_settings = RuntimeSettings("PAPER", "paper", settings)
live_settings = RuntimeSettings("LIVE", "live", settings)
