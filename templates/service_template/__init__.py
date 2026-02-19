"""TODO: <Service Name> service plugin.

Exposes :class:`TemplateService`, which satisfies the
:class:`~nasa_apod.services.base.ServicePlugin` protocol and
registers all TODO: <Service Name> tools and resources onto a
FastMCP server instance.

TODO: Rename TemplateService to match your service (e.g. MarsRoverService).
"""

from mcp.server.fastmcp import FastMCP

from nasa_apod.services.base import ServicePlugin  # noqa: F401 (for type reference)

__all__ = ["TemplateService"]


class TemplateService:
    """ServicePlugin for TODO: <Your API>.

    Composes a client and formatter, then registers MCP tools and
    resources in :meth:`register`.

    TODO:
      1. Rename this class (e.g. MarsRoverService)
      2. Import your client and formatter classes
      3. Import your config constants
      4. Create client and formatter instances in __init__
      5. Define your tools inside register()
    """

    def __init__(self) -> None:
        """Initialize the service with its client and formatter.

        TODO: Uncomment and update these lines after creating your
        client and formatter:

        from nasa_apod.services.<your_service>.client import YourClient
        from nasa_apod.services.<your_service>.config import (
            API_BASE_URL,
            API_KEY,
            REQUEST_TIMEOUT_SECONDS,
        )
        from nasa_apod.services.<your_service>.formatter import YourFormatter

        self._client = YourClient(
            base_url=API_BASE_URL,
            api_key=API_KEY,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        self._formatter = YourFormatter()
        """

    def register(self, mcp: FastMCP) -> None:
        """Register tools and resources onto the FastMCP server.

        Args:
            mcp: The FastMCP server instance to register onto.

        TODO: Define your tools and resources below. Each tool is a
        decorated async function. Each resource is a decorated sync
        function. See the examples below and the APOD service for
        a complete working implementation.
        """

        @mcp.tool()
        async def get_template_data() -> str:
            """TODO: Describe what this tool does.

            Write a clear, specific docstring. The AI agent reads this
            to decide when to call the tool. Mention:
            - What the tool returns
            - When to use it
            - Any parameter formats or constraints

            TODO: Rename this function and implement the body.
            """
            return "TODO: Implement this tool."

        @mcp.resource("todo://replace/with-your-uri")
        def template_reference_data() -> str:
            """TODO: Describe what this resource provides.

            Resources are read-only data the AI agent can access.
            Good for: reference lists, schemas, documentation.

            TODO: Rename this function and implement the body.
            """
            return "TODO: Return your reference data here."
