"""APOD HTTP client extending BaseAPIClient.

Encapsulates all network communication with the NASA APOD REST API.
Uses ``httpx`` for non-blocking I/O and structured ``logging``.
"""

import logging
from typing import Any

import httpx

from nasa_apod.services.base import BaseAPIClient

logger = logging.getLogger(__name__)


class ApodClient(BaseAPIClient):
    """Async HTTP client for the NASA Astronomy Picture of the Day API.

    Extends :class:`~nasa_apod.services.base.BaseAPIClient` with
    APOD-specific request logic. The ``fetch`` method accepts an
    optional ``date`` keyword to query a specific archive entry.
    """

    async def fetch(self, **params: str) -> dict[str, Any] | None:
        """Fetch a single APOD entry from NASA.

        Args:
            **params: Optional query parameters. Pass ``date="YYYY-MM-DD"``
                      to request a specific archive entry. When omitted the
                      API returns today's entry.

        Returns:
            Parsed JSON dictionary on success, or ``None`` on failure.
        """
        query: dict[str, str] = {"api_key": self.api_key}
        query.update(params)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.base_url,
                    params=query,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "NASA API returned HTTP %s for params=%s: %s",
                    exc.response.status_code,
                    params,
                    exc.response.text[:200],
                )
                return None
            except httpx.RequestError as exc:
                logger.error(
                    "Network error while fetching APOD for params=%s: %s",
                    params,
                    exc,
                )
                return None
