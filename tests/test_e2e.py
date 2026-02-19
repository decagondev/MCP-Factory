"""End-to-end tests for the MCP server.

Verifies the full server boots correctly, all tools are registered
with expected names, each tool returns the correct output format when
called through the FastMCP interface (with mocked HTTP), and the
famous-dates resource is accessible.
"""

import httpx
import pytest
import respx

from nasa_apod.services.apod.config import NASA_APOD_BASE_URL

SAMPLE_APOD: dict = {
    "title": "E2E Test Nebula",
    "date": "2024-06-15",
    "explanation": "A spectacular nebula captured for end-to-end testing.",
    "media_type": "image",
    "url": "https://apod.nasa.gov/apod/image/2406/e2e_nebula.jpg",
    "copyright": "Test Photographer",
}

EXPECTED_TOOL_NAMES: set[str] = {
    "get_todays_space_photo",
    "get_space_photo_by_date",
    "get_random_space_photo",
}


@pytest.fixture()
def mcp_server():
    """Provide a fresh FastMCP server instance with all plugins applied.

    Builds a new server each time so tests don't share mutable state
    from the module-level singleton.
    """
    from mcp.server.fastmcp import FastMCP

    from nasa_apod.config import SERVER_NAME
    from nasa_apod.services.apod import ApodService
    from nasa_apod.services.registry import ServiceRegistry

    server = FastMCP(SERVER_NAME)
    registry = ServiceRegistry()
    registry.add(ApodService())
    registry.apply_all(server)
    return server


class TestServerBootstrap:
    """Verify the server boots and all expected tools/resources exist."""

    @pytest.mark.asyncio
    async def test_all_three_tools_registered(self, mcp_server) -> None:
        tools = await mcp_server.list_tools()
        tool_names = {t.name for t in tools}
        assert tool_names == EXPECTED_TOOL_NAMES

    @pytest.mark.asyncio
    async def test_famous_dates_resource_registered(self, mcp_server) -> None:
        resources = await mcp_server.list_resources()
        uris = {str(r.uri) for r in resources}
        assert "space://events/famous-dates" in uris


@pytest.mark.asyncio
class TestToolExecution:
    """Call each tool through the FastMCP interface with mocked HTTP."""

    @respx.mock
    async def test_get_todays_space_photo(self, mcp_server) -> None:
        respx.get(NASA_APOD_BASE_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_APOD)
        )
        result_tuple = await mcp_server.call_tool("get_todays_space_photo", {})
        text = result_tuple[0][0].text

        assert SAMPLE_APOD["title"] in text
        assert SAMPLE_APOD["date"] in text
        assert SAMPLE_APOD["url"] in text
        assert "Test Photographer" in text

    @respx.mock
    async def test_get_space_photo_by_date(self, mcp_server) -> None:
        respx.get(NASA_APOD_BASE_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_APOD)
        )
        result_tuple = await mcp_server.call_tool(
            "get_space_photo_by_date", {"date": "2024-06-15"}
        )
        text = result_tuple[0][0].text

        assert SAMPLE_APOD["title"] in text
        assert SAMPLE_APOD["explanation"] in text

    @respx.mock
    async def test_get_random_space_photo(self, mcp_server) -> None:
        respx.get(NASA_APOD_BASE_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_APOD)
        )
        result_tuple = await mcp_server.call_tool("get_random_space_photo", {})
        text = result_tuple[0][0].text

        assert "Random Space Photo Discovery" in text
        assert SAMPLE_APOD["title"] in text

    @respx.mock
    async def test_photo_by_date_validates_bad_format(self, mcp_server) -> None:
        result_tuple = await mcp_server.call_tool(
            "get_space_photo_by_date", {"date": "not-a-date"}
        )
        text = result_tuple[0][0].text
        assert "YYYY-MM-DD" in text

    @respx.mock
    async def test_photo_by_date_validates_future_date(self, mcp_server) -> None:
        result_tuple = await mcp_server.call_tool(
            "get_space_photo_by_date", {"date": "2099-12-31"}
        )
        text = result_tuple[0][0].text
        assert "today" in text

    @respx.mock
    async def test_todays_photo_handles_api_failure(self, mcp_server) -> None:
        respx.get(NASA_APOD_BASE_URL).mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        result_tuple = await mcp_server.call_tool("get_todays_space_photo", {})
        text = result_tuple[0][0].text
        assert "Unable to fetch" in text


class TestResourceAccess:
    """Verify resources are readable through the FastMCP interface."""

    @pytest.mark.asyncio
    async def test_famous_dates_resource_content(self, mcp_server) -> None:
        result = await mcp_server.read_resource("space://events/famous-dates")
        content = result[0].content

        assert "1995-06-16" in content
        assert "Moon Landing" in content
        assert "James Webb" in content
