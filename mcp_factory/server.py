"""MCP server construction using the service registry.

Creates the ``FastMCP`` instance, instantiates the
:class:`~mcp_factory.services.registry.ServiceRegistry`, loads all
service plugins, and applies them. Adding a new API service means
importing it here and calling ``registry.add(...)`` -- no other file
needs to change.
"""

from mcp.server.fastmcp import FastMCP

from mcp_factory.config import SERVER_NAME
from mcp_factory.services.apod import ApodService
from mcp_factory.services.code_guardian import CodeGuardianService
from mcp_factory.services.registry import ServiceRegistry

mcp = FastMCP(SERVER_NAME)

registry = ServiceRegistry()
registry.add(ApodService())
registry.add(CodeGuardianService())
registry.apply_all(mcp)
