from __future__ import annotations

import os
from datetime import UTC, date, datetime, tzinfo
from zoneinfo import ZoneInfo


def local_timezone() -> tzinfo:
    tz_name = os.environ.get("DECKFLOW_TZ")
    if tz_name:
        return ZoneInfo(tz_name)
    tzinfo_value = datetime.now().astimezone().tzinfo
    return tzinfo_value or UTC


def local_now(now: datetime | None = None) -> datetime:
    tz = local_timezone()
    if now is None:
        return datetime.now(tz)
    if now.tzinfo is None:
        return now.replace(tzinfo=UTC).astimezone(tz)
    return now.astimezone(tz)


def local_day_start(now: datetime | None = None) -> datetime:
    """UTC-aware instant for local midnight at the start of the local calendar day."""
    local = local_now(now)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.astimezone(UTC)


def local_today(now: datetime | None = None) -> date:
    return local_now(now).date()


def reviewed_at_local_date(reviewed_at: str) -> date:
    reviewed = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    if reviewed.tzinfo is None:
        reviewed = reviewed.replace(tzinfo=UTC)
    return reviewed.astimezone(local_timezone()).date()
