from datetime import datetime, time, timezone


def parse_entry_time_utc(entry_time: str) -> time:
    parts = entry_time.split(":")
    if len(parts) != 2:
        raise ValueError("ENTRY_TIME_UTC must be HH:MM")
    hour = int(parts[0])
    minute = int(parts[1])
    return time(hour=hour, minute=minute, tzinfo=timezone.utc)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
