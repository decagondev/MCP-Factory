"""APOD-specific configuration constants.

All values that are particular to the Astronomy Picture of the Day API
live here. Global/shared settings remain in ``nasa_apod.config``.
"""

import os
from datetime import datetime

NASA_APOD_BASE_URL: str = "https://api.nasa.gov/planetary/apod"
"""Base URL for the NASA APOD REST API."""

NASA_API_KEY: str = os.environ.get("NASA_API_KEY", "DEMO_KEY")
"""NASA API key. Override via the ``NASA_API_KEY`` environment variable.

The default ``DEMO_KEY`` is rate-limited to 30 requests/hour and
50 requests/day per IP.
"""

FIRST_APOD_DATE: datetime = datetime(1995, 6, 16)
"""The date of the very first Astronomy Picture of the Day."""

DATE_FORMAT: str = "%Y-%m-%d"
"""Expected date string format for APOD queries."""

REQUEST_TIMEOUT_SECONDS: float = 30.0
"""HTTP request timeout in seconds for APOD API calls."""
