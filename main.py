"""MCP Factory entry point.

Starts the MCP server over stdio transport. All tool and resource
definitions live in the ``mcp_factory`` package; this module exists
solely so that ``uv run main.py`` continues to work as the
documented launch command.
"""

from mcp_factory.server import mcp


def main() -> None:
    """Run the MCP Factory server over stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
