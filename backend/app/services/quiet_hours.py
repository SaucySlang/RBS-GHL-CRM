"""Quiet-hours windows per sub-account.

Each sub-account configures a timezone and a local send window
(e.g. 08:00–20:00). Outbound steps firing outside the window are paused and
rescheduled for the moment the window reopens.
"""
from datetime import datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo


def _parse_hhmm(value: str, fallback: time) -> time:
    try:
        hour, minute = value.split(":")
        return time(int(hour), int(minute))
    except (ValueError, AttributeError):
        return fallback


def next_send_time(sub_account, now_utc: Optional[datetime] = None) -> Optional[datetime]:
    """Return None if sending is allowed right now, otherwise the UTC
    datetime when the sub-account's local send window next opens."""
    now_utc = now_utc or datetime.utcnow()

    try:
        tz = ZoneInfo(sub_account.timezone or "UTC")
    except Exception:
        tz = ZoneInfo("UTC")

    window_start = _parse_hhmm(sub_account.quiet_hours_start, time(8, 0))
    window_end = _parse_hhmm(sub_account.quiet_hours_end, time(20, 0))

    local_now = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
    local_time = local_now.time()

    if window_start <= window_end:
        in_window = window_start <= local_time < window_end
    else:
        # Window wraps midnight (e.g. 22:00–06:00)
        in_window = local_time >= window_start or local_time < window_end

    if in_window:
        return None

    # Compute the next window opening in local time
    open_today = local_now.replace(
        hour=window_start.hour, minute=window_start.minute, second=0, microsecond=0
    )
    next_open = open_today if local_now < open_today else open_today + timedelta(days=1)

    return next_open.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
