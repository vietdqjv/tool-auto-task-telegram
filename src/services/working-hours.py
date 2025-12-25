# src/services/working-hours.py
"""Working hours utility for VN timezone."""
import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from src.core.config import settings

TIMEZONE = ZoneInfo(settings.TIMEZONE)


def is_working_time(dt: datetime | None = None) -> bool:
    """Check if datetime falls within working hours.

    Returns False during:
    - Lunch break (12:00-13:30)
    - After hours (before 8:30 or after 17:30)
    - Weekends (Saturday, Sunday)
    """
    if dt is None:
        dt = datetime.now(TIMEZONE)

    # Convert to local timezone if needed
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TIMEZONE)
    else:
        dt = dt.astimezone(TIMEZONE)

    # Check weekday (Mon=0, Sun=6)
    if dt.weekday() not in settings.WORKING_DAYS:
        return False

    current_time = dt.time()
    for start_h, start_m, end_h, end_m in settings.WORKING_PERIODS:
        start = time(start_h, start_m)
        end = time(end_h, end_m)
        if start <= current_time <= end:
            return True
    return False


def get_next_working_time(dt: datetime | None = None) -> datetime:
    """Get next valid working time.

    Handles:
    - During lunch (12:00-13:30) -> 13:30 same day
    - After 17:30 -> 8:30 next working day
    - Weekend -> 8:30 Monday
    - Before 8:30 -> 8:30 same day
    """
    if dt is None:
        dt = datetime.now(TIMEZONE)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TIMEZONE)
    else:
        dt = dt.astimezone(TIMEZONE)

    # Get working period boundaries
    morning_start = time(settings.WORKING_PERIODS[0][0], settings.WORKING_PERIODS[0][1])
    morning_end = time(settings.WORKING_PERIODS[0][2], settings.WORKING_PERIODS[0][3])
    afternoon_start = time(settings.WORKING_PERIODS[1][0], settings.WORKING_PERIODS[1][1])
    afternoon_end = time(settings.WORKING_PERIODS[1][2], settings.WORKING_PERIODS[1][3])

    current_time = dt.time()

    # Already in working time
    if is_working_time(dt):
        return dt

    # Check if it's a working day
    if dt.weekday() in settings.WORKING_DAYS:
        # Before morning start -> morning start same day
        if current_time < morning_start:
            return dt.replace(
                hour=morning_start.hour, minute=morning_start.minute,
                second=0, microsecond=0
            )
        # During lunch -> afternoon start same day
        if morning_end < current_time < afternoon_start:
            return dt.replace(
                hour=afternoon_start.hour, minute=afternoon_start.minute,
                second=0, microsecond=0
            )

    # After hours or weekend -> next working day morning
    next_day = dt + timedelta(days=1)
    while next_day.weekday() not in settings.WORKING_DAYS:
        next_day += timedelta(days=1)

    return next_day.replace(
        hour=morning_start.hour, minute=morning_start.minute,
        second=0, microsecond=0
    )


def parse_reminder_interval(text: str) -> int | None:
    """Parse natural format like '2h', '30m', '1h30m' to minutes.

    Args:
        text: Interval string (e.g., "2h", "30m", "1h30m")

    Returns:
        Total minutes or None if invalid format
    """
    pattern = r'(?:(\d+)h)?(?:(\d+)m)?'
    match = re.fullmatch(pattern, text.strip().lower())
    if not match or not any(match.groups()):
        return None

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    total = hours * 60 + minutes

    # Enforce minimum interval
    if total < settings.MIN_REMINDER_INTERVAL:
        return None

    return total
