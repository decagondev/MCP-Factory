"""APOD service plugin.

Exposes :class:`ApodService`, which satisfies the
:class:`~mcp_factory.services.base.ServicePlugin` protocol and
registers all Astronomy Picture of the Day tools and resources
onto a FastMCP server instance.
"""

import random
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

from mcp_factory.services.apod.client import ApodClient
from mcp_factory.services.apod.config import (
    FIRST_APOD_DATE,
    NASA_APOD_BASE_URL,
    NASA_API_KEY,
    REQUEST_TIMEOUT_SECONDS,
)
from mcp_factory.services.apod.formatter import ApodFormatter
from mcp_factory.services.apod.validation import validate_apod_date

__all__ = ["ApodService"]


class ApodService:
    """APOD ServicePlugin -- registers all APOD tools and resources.

    Composes an :class:`ApodClient` and :class:`ApodFormatter`, then
    registers three MCP tools and one resource onto the server.  The
    tool names, parameter signatures, and return formats are identical
    to the pre-refactor versions so there are no breaking changes.
    """

    def __init__(self) -> None:
        self._client = ApodClient(
            base_url=NASA_APOD_BASE_URL,
            api_key=NASA_API_KEY,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        self._formatter = ApodFormatter()

    def register(self, mcp: FastMCP) -> None:
        """Register APOD tools and the famous-dates resource onto *mcp*.

        Args:
            mcp: The FastMCP server instance to register onto.
        """
        client = self._client
        formatter = self._formatter

        @mcp.tool()
        async def get_todays_space_photo() -> str:
            """Get today's Astronomy Picture of the Day from NASA."""
            data = await client.fetch()
            if not data:
                return "\u274c Unable to fetch today's space photo."
            return formatter.format(data)

        @mcp.tool()
        async def get_space_photo_by_date(date: str) -> str:
            """Get the Astronomy Picture of the Day for a specific date (YYYY-MM-DD)."""
            result = validate_apod_date(date)
            if isinstance(result, str):
                return result

            data = await client.fetch(date=date)
            if not data:
                return f"\u274c Unable to fetch space photo for {date}"
            return formatter.format(data)

        @mcp.tool()
        async def get_random_space_photo() -> str:
            """Get a random Astronomy Picture of the Day from NASA's archives."""
            today = datetime.now()
            days_diff = (today - FIRST_APOD_DATE).days

            random_days = random.randint(0, days_diff)
            random_date = FIRST_APOD_DATE + timedelta(days=random_days)
            random_date_str = random_date.strftime("%Y-%m-%d")

            data = await client.fetch(date=random_date_str)
            if not data:
                return "\u274c Unable to fetch random space photo. Please try again."
            return formatter.format(
                data,
                header="\U0001f3b2 **Random Space Photo Discovery!**",
            )

        @mcp.resource("space://events/famous-dates")
        def famous_space_dates() -> str:
            """List of famous space exploration dates to explore in APOD archives."""
            return (
                "\nFamous Space Dates to Explore:\n\n"
                "\U0001f680 First APOD: 1995-06-16\n"
                "\U0001f319 Moon Landing: 1969-07-20\n"
                "\U0001f6f8 Hubble Launch: 1990-04-24\n"
                "\U0001f534 Mars Rover Landing: 2021-02-18\n"
                "\U0001f31f First Image of Black Hole: 2019-04-10\n"
                "\U0001fa90 Cassini Saturn Arrival: 2004-07-01\n"
                "\u2604\ufe0f Rosetta Comet Landing: 2014-11-12\n"
                "\U0001f6f0\ufe0f Voyager 1 Jupiter Flyby: 1979-03-05\n"
                "\U0001f30d Earth Day: 1970-04-22\n"
                "\U0001f52d James Webb First Image: 2022-07-12\n"
            )
