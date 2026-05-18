"""Time conversion utilities for ephemeris calculations."""

from __future__ import annotations

from datetime import datetime, timezone


def parse_utc_datetime(dt_iso: str) -> datetime:
    """Parse ISO datetime to timezone-aware UTC datetime."""
    normalized = dt_iso.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def julian_date_from_datetime_utc(dt_utc: datetime) -> float:
    """Convert UTC datetime to Julian Date."""
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    else:
        dt_utc = dt_utc.astimezone(timezone.utc)
    unix_seconds = dt_utc.timestamp()
    return float(unix_seconds / 86400.0 + 2440587.5)

