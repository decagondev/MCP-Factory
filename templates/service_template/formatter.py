"""Response formatter for the TODO: <Service Name> service.

Converts raw API data into the user-facing Markdown string returned
by MCP tools.

TODO: Rename the class and implement the format() method for your API's
response schema.
"""

from typing import Any

from nasa_apod.services.base import BaseFormatter


class TemplateFormatter(BaseFormatter):
    """Formats TODO: <Your API> responses into Markdown.

    Extends :class:`~nasa_apod.services.base.BaseFormatter` with
    field handling specific to your API's response schema.

    TODO: Rename this class to match your service (e.g. MarsRoverFormatter).
    """

    def format(self, data: dict[str, Any], **kwargs: Any) -> str:
        """Format raw API data into a Markdown response string.

        Args:
            data: Dictionary returned by your API.
                  TODO: Document the expected fields.
            **kwargs: Optional formatting options (e.g. ``header``).

        Returns:
            A Markdown-formatted string for the MCP client.
        """
        header: str | None = kwargs.get("header")
        parts: list[str] = []

        if header:
            parts.append(header)
            parts.append("")

        parts.append(f"**{data.get('title', 'Untitled')}**")
        parts.append(f"Description: {data.get('description', 'No description available.')}")

        return "\n".join(parts)
