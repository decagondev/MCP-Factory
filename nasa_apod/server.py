"""MCP server construction using the service registry.

Creates the ``FastMCP`` instance, instantiates the
:class:`~nasa_apod.services.registry.ServiceRegistry`, loads all
service plugins, and applies them. Adding a new API service means
importing it here and calling ``registry.add(...)`` -- no other file
needs to change.
"""

from mcp.server.fastmcp import FastMCP

from nasa_apod.config import SERVER_NAME
from nasa_apod.services.apod import ApodService
from nasa_apod.services.code_guardian import CodeGuardianService
from nasa_apod.services.registry import ServiceRegistry

mcp = FastMCP(SERVER_NAME)

registry = ServiceRegistry()
registry.add(ApodService())
registry.add(CodeGuardianService())
registry.apply_all(mcp)
