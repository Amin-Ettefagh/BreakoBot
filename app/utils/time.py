from datetime import datetime, time as dtime, timedelta


def seconds_until_next_midnight() -> float:
    """Return seconds until next midnight (server local time)."""
    now = datetime.now()
    next_midnight = datetime.combine(now.date() + timedelta(days=1), dtime(0, 0, 5))
    return max((next_midnight - now).total_seconds(), 1.0)
