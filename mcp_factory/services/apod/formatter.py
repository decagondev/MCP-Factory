"""APOD response formatter extending BaseFormatter.

Converts raw NASA APOD API data into the user-facing Markdown string
returned by every APOD MCP tool.
"""

from typing import Any

from mcp_factory.services.base import BaseFormatter


class ApodFormatter(BaseFormatter):
    """Formats APOD API responses into Markdown.

    Extends :class:`~mcp_factory.services.base.BaseFormatter` with
    APOD-specific field handling (title, date, explanation, media_type,
    url, and optional copyright).
    """

    def format(self, data: dict[str, Any], **kwargs: Any) -> str:
        """Format raw APOD data into a Markdown response string.

        Args:
            data: Dictionary returned by the NASA APOD API containing at
                  least ``title``, ``date``, ``explanation``, ``media_type``,
                  and ``url``.
            **kwargs: Optional ``header`` string prepended above the title.

        Returns:
            A Markdown-formatted string ready for the MCP client.
        """
        header: str | None = kwargs.get("header")
        parts: list[str] = []

        if header:
            parts.append(header)
            parts.append("")

        parts.append(f"\U0001f30c **{data['title']}**")
        parts.append(f"\U0001f4c5 Date: {data['date']}")
        parts.append("")
        parts.append("**What you're seeing:**")
        parts.append(data["explanation"])
        parts.append("")
        parts.append(f"**Media:** {data['media_type'].title()}")
        parts.append(f"\U0001f517 {data['url']}")

        if "copyright" in data:
            parts.append(f"\n\U0001f4f8 Copyright: {data['copyright']}")

        return "\n".join(parts)
