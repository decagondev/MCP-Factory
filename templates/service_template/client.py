"""HTTP client for the TODO: <Service Name> service.

Encapsulates all network communication with the external API.
Uses ``httpx`` for non-blocking I/O and structured ``logging``.

TODO: Rename the class and implement the fetch() method for your API.
"""

import logging
from typing import Any

import httpx

from nasa_apod.services.base import BaseAPIClient

logger = logging.getLogger(__name__)


class TemplateClient(BaseAPIClient):
    """Async HTTP client for TODO: <Your API Name>.

    Extends :class:`~nasa_apod.services.base.BaseAPIClient` with
    request logic specific to your API.

    TODO: Rename this class to match your service (e.g. MarsRoverClient).
    """

    async def fetch(self, **params: str) -> dict[str, Any] | None:
        """Fetch data from the API.

        Args:
            **params: Query parameters forwarded to the API endpoint.
                      TODO: Document the specific parameters your API accepts.

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
                    "API returned HTTP %s: %s",
                    exc.response.status_code,
                    exc.response.text[:200],
                )
                return None
            except httpx.RequestError as exc:
                logger.error("Network error reaching API: %s", exc)
                return None
