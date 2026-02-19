"""Base abstractions for API service plugins.

Defines the contracts that every API service must satisfy:

- ``BaseAPIClient`` -- async HTTP client with configurable endpoint
- ``BaseFormatter`` -- converts raw API data into Markdown for MCP tools
- ``ServicePlugin`` -- structural protocol for registering tools onto FastMCP

New services extend ``BaseAPIClient`` and ``BaseFormatter``, then expose
a class satisfying ``ServicePlugin`` so the registry can wire everything
into the server automatically.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from mcp.server.fastmcp import FastMCP


class BaseAPIClient(ABC):
    """Contract for all API service HTTP clients.

    Subclasses must implement :meth:`fetch` to perform the actual
    network request and return parsed JSON (or ``None`` on failure).

    Args:
        base_url: Root URL of the API endpoint.
        api_key: Authentication key sent with every request.
        timeout: HTTP request timeout in seconds.
    """

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    @abstractmethod
    async def fetch(self, **params: str) -> dict[str, Any] | None:
        """Fetch data from the API.

        Args:
            **params: Arbitrary keyword arguments forwarded as query
                      parameters (e.g. ``date="2024-01-15"``).

        Returns:
            Parsed JSON dictionary on success, or ``None`` when the
            request fails for any reason.
        """


class BaseFormatter(ABC):
    """Contract for all API response formatters.

    Subclasses must implement :meth:`format` to convert a raw API
    response dictionary into the Markdown string returned to the
    MCP client.
    """

    @abstractmethod
    def format(self, data: dict[str, Any], **kwargs: Any) -> str:
        """Format API response data into a Markdown string.

        Args:
            data: Parsed JSON dictionary from the API.
            **kwargs: Additional formatting options (e.g. ``header``).

        Returns:
            A Markdown-formatted string ready for the MCP client.
        """


class ServicePlugin(Protocol):
    """Structural protocol for service plugins.

    Any class with a ``register(mcp)`` method satisfies this protocol.
    The :class:`~mcp_factory.services.registry.ServiceRegistry` uses it
    to wire each service's tools and resources into the FastMCP server.
    """

    def register(self, mcp: FastMCP) -> None:
        """Register this service's tools and resources onto *mcp*.

        Args:
            mcp: The FastMCP server instance to register onto.
        """
        ...
