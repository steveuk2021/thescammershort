from datetime import datetime, timedelta, timezone

from .time_utils import parse_entry_time_utc


def within_entry_window(entry_time_utc: str, window_minutes: int = 60) -> bool:
    now = datetime.now(timezone.utc)
    entry_time = parse_entry_time_utc(entry_time_utc)
    today_entry = datetime.combine(now.date(), entry_time)
    window_end = today_entry + timedelta(minutes=window_minutes)
    return today_entry <= now <= window_end
