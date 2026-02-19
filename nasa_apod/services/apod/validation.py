"""Date validation for APOD queries.

Isolates all date-parsing and range-checking logic so that tool
functions stay thin orchestrators and validation rules live in
exactly one place.
"""

from datetime import datetime

from nasa_apod.services.apod.config import DATE_FORMAT, FIRST_APOD_DATE


def validate_apod_date(date_str: str) -> datetime | str:
    """Parse and validate a date string for the APOD archive.

    Args:
        date_str: A date string expected to be in ``YYYY-MM-DD`` format.

    Returns:
        The parsed ``datetime`` on success, or a human-readable error
        message string when the input is malformed or out of the valid
        APOD range (1995-06-16 through today).
    """
    try:
        parsed = datetime.strptime(date_str, DATE_FORMAT)
    except ValueError:
        return "\u274c Invalid date format. Use YYYY-MM-DD"

    if parsed < FIRST_APOD_DATE:
        return "\u274c Date must be between 1995-06-16 and today"

    if parsed > datetime.now():
        return "\u274c Date must be between 1995-06-16 and today"

    return parsed
