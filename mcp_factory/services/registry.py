"""Service registry -- factory for collecting and applying service plugins.

The registry is the single integration point between the FastMCP server
and all API service plugins. Services are added with :meth:`add` and
then bulk-applied with :meth:`apply_all`, keeping the server module
free of per-service wiring.
"""

import logging

from mcp.server.fastmcp import FastMCP

from mcp_factory.services.base import ServicePlugin

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Collects :class:`ServicePlugin` instances and applies them to a FastMCP server.

    Usage::

        registry = ServiceRegistry()
        registry.add(ApodService())
        registry.add(MarsRoverService())   # future service
        registry.apply_all(mcp)
    """

    def __init__(self) -> None:
        self._plugins: list[ServicePlugin] = []

    def add(self, plugin: ServicePlugin) -> None:
        """Register a service plugin for later application.

        Args:
            plugin: Any object satisfying the :class:`ServicePlugin` protocol.
        """
        self._plugins.append(plugin)
        logger.info("Registered service plugin: %s", type(plugin).__name__)

    def apply_all(self, mcp: FastMCP) -> None:
        """Apply every registered plugin to the FastMCP server.

        Calls ``plugin.register(mcp)`` for each plugin in registration order.

        Args:
            mcp: The FastMCP server instance.
        """
        for plugin in self._plugins:
            plugin.register(mcp)
            logger.info("Applied service plugin: %s", type(plugin).__name__)

    @property
    def plugins(self) -> list[ServicePlugin]:
        """Read-only view of registered plugins (useful for testing)."""
        return list(self._plugins)
