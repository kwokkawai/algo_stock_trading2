"""Trading session helpers — HK regular hours for intraday runner."""

from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

HK_TZ = ZoneInfo("Asia/Hong_Kong")

# HK regular session (Mon–Fri)
HK_MORNING = (time(9, 30), time(12, 0))
HK_AFTERNOON = (time(13, 0), time(16, 0))


def is_hk_trading_session(now: datetime | None = None) -> bool:
    """Return True during HK equity regular trading hours (weekdays)."""
    now = now or datetime.now(HK_TZ)
    if now.tzinfo is None:
        now = now.replace(tzinfo=HK_TZ)
    else:
        now = now.astimezone(HK_TZ)

    if now.weekday() >= 5:  # Sat/Sun
        return False

    t = now.time()
    return _in_range(t, *HK_MORNING) or _in_range(t, *HK_AFTERNOON)


def is_trading_session(market: str, now: datetime | None = None) -> bool:
    """Market-aware session check. US not implemented — returns True (no gate)."""
    if market.upper() == "HK":
        return is_hk_trading_session(now)
    return True


def _in_range(t: time, start: time, end: time) -> bool:
    return start <= t < end
