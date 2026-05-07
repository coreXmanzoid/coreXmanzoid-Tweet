from datetime import datetime, timezone, timedelta


def utc_now():
    return datetime.now(timezone.utc)


def utc_iso():
    return datetime.now(timezone.utc).isoformat()


def add_minutes(minutes):
    return utc_now() + timedelta(minutes=minutes)


def add_hours(hours):
    return utc_now() + timedelta(hours=hours)


def add_days(days):
    return utc_now() + timedelta(days=days)


def ensure_utc(value):
    if value is None:
        return None

    if value.tzinfo is None:
        # Existing SQLite rows can come back naive; treat them as UTC before comparing.
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def utc_iso_from(value):
    value = ensure_utc(value)
    return value.isoformat() if value else None
