"""Timezone utility module for Asia/Tehran and UTC conversions.

Guarantees accurate IANA timezone handling for Asia/Tehran across all platforms.
"""

from datetime import datetime, timezone, tzinfo
from typing import Optional, Union
import dateutil.parser
from dateutil import tz


def get_tehran_timezone() -> tzinfo:
    """Get the IANA Asia/Tehran timezone object with fallback."""
    # First try Python's standard zoneinfo
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Asia/Tehran")
    except Exception:
        pass

    # Fallback to dateutil.tz which supports IANA tzfile/zone data cross-platform
    tehran_tz = tz.gettz("Asia/Tehran")
    if tehran_tz is not None:
        return tehran_tz

    # Safety fallback (should never occur with dateutil installed)
    raise RuntimeError("Unable to load IANA Asia/Tehran timezone")


TEHRAN_TZ = get_tehran_timezone()
UTC_TZ = timezone.utc


def now_utc() -> datetime:
    """Get the current time as a UTC-aware datetime."""
    return datetime.now(UTC_TZ)


def now_tehran() -> datetime:
    """Get the current time in Asia/Tehran timezone."""
    return datetime.now(get_tehran_timezone())


def to_utc(dt_val: Union[datetime, str]) -> datetime:
    """Convert any datetime or ISO string to a UTC-aware datetime.
    
    If the datetime is naive (no timezone info), it is treated as local Asia/Tehran time
    and converted to UTC.
    """
    if isinstance(dt_val, str):
        parsed = dateutil.parser.isoparse(dt_val)
    elif isinstance(dt_val, datetime):
        parsed = dt_val
    else:
        raise ValueError(f"Unsupported datetime value: {dt_val}")

    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        # Naive datetime: interpret as Asia/Tehran
        tehran = get_tehran_timezone()
        parsed = parsed.replace(tzinfo=tehran)

    return parsed.astimezone(UTC_TZ)


def to_tehran(dt_val: Union[datetime, str]) -> datetime:
    """Convert any datetime or ISO string to an Asia/Tehran timezone-aware datetime."""
    utc_dt = to_utc(dt_val)
    return utc_dt.astimezone(get_tehran_timezone())


def format_tehran_iso(dt_val: Union[datetime, str]) -> str:
    """Format a datetime as an ISO-8601 string in Asia/Tehran timezone."""
    tehran_dt = to_tehran(dt_val)
    return tehran_dt.isoformat()


def get_offer_status(
    start_at: Union[datetime, str],
    end_at: Union[datetime, str],
    is_active: bool,
    reference_time: Optional[Union[datetime, str]] = None,
) -> str:
    """Compute the dynamic lifecycle status of a special offer.
    
    Returns:
        - 'inactive': if is_active is False
        - 'upcoming': if current_time < start_at
        - 'active': if start_at <= current_time < end_at and is_active is True
        - 'expired': if current_time >= end_at
    """
    if not is_active:
        return "inactive"

    start_utc = to_utc(start_at)
    end_utc = to_utc(end_at)
    curr_utc = to_utc(reference_time) if reference_time is not None else now_utc()

    if curr_utc < start_utc:
        return "upcoming"
    elif curr_utc >= end_utc:
        return "expired"
    else:
        return "active"
