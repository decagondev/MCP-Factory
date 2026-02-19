"""OSV (Open Source Vulnerabilities) API client.

Extends :class:`~mcp_factory.services.base.BaseAPIClient` to query
the `OSV.dev <https://osv.dev/>`_ vulnerability database.  OSV is
free and requires no authentication.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from mcp_factory.services.base import BaseAPIClient

logger = logging.getLogger(__name__)


class OsvClient(BaseAPIClient):
    """Async HTTP client for the OSV.dev vulnerability API.

    Extends :class:`~mcp_factory.services.base.BaseAPIClient` with
    POST-based query semantics required by the OSV REST API.

    The ``fetch`` method accepts ``name`` and ``ecosystem`` keyword
    arguments and returns a list of vulnerability records (or
    ``None`` on error).
    """

    async def fetch(self, **params: str) -> dict[str, Any] | None:
        """Query OSV for vulnerabilities affecting a given package.

        Args:
            **params: Must include ``name`` (package name) and
                      ``ecosystem`` (e.g. ``"PyPI"``, ``"npm"``).
                      Optionally include ``version`` for an exact
                      version match.

        Returns:
            Parsed JSON response containing a ``vulns`` list on
            success, or ``None`` on failure.
        """
        name = params.get("name", "")
        ecosystem = params.get("ecosystem", "")
        version = params.get("version", "")

        if not name or not ecosystem:
            logger.error("OsvClient.fetch requires 'name' and 'ecosystem'")
            return None

        payload: dict[str, Any] = {
            "package": {
                "name": name,
                "ecosystem": ecosystem,
            }
        }
        if version:
            payload["version"] = version

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/query",
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "OSV API returned HTTP %s for package %s/%s: %s",
                    exc.response.status_code,
                    ecosystem,
                    name,
                    exc.response.text[:200],
                )
                return None
            except httpx.RequestError as exc:
                logger.error(
                    "Network error querying OSV for %s/%s: %s",
                    ecosystem,
                    name,
                    exc,
                )
                return None
