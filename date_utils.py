"""Date parsing helpers shared by the calendar import and storage code."""

from datetime import date, datetime


def parse_event_date(value: str) -> str:
    """Return an ISO date from a date or ISO datetime string."""
    value = value.strip()
    try:
        if "T" in value:
            parsed_date = datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        else:
            parsed_date = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"Invalid date: {value}. Use YYYY-MM-DD.") from error
    return parsed_date.isoformat()