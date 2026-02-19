"""Global configuration for the MCP server.

Contains only server-wide settings. Service-specific configuration
(API keys, base URLs, timeouts) lives inside each service's own
``config.py`` under ``nasa_apod.services.<name>``.
"""

SERVER_NAME: str = "mcp-factory"
"""Name used when creating the FastMCP server instance."""
