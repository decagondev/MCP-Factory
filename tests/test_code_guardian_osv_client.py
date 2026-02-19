"""Tests for mcp_factory.services.code_guardian.osv_client using respx."""

import httpx
import pytest
import respx

from mcp_factory.services.code_guardian.config import OSV_API_BASE_URL
from mcp_factory.services.code_guardian.osv_client import OsvClient


def _make_client() -> OsvClient:
    """Create an OsvClient wired to the real OSV base URL for testing."""
    return OsvClient(base_url=OSV_API_BASE_URL, api_key="", timeout=10.0)


SAMPLE_VULN_RESPONSE: dict = {
    "vulns": [
        {
            "id": "GHSA-1234-5678-abcd",
            "summary": "Critical vulnerability in example-package",
            "severity": [{"type": "CVSS_V3", "score": "9.8"}],
        }
    ]
}

EMPTY_RESPONSE: dict = {"vulns": []}


@pytest.mark.asyncio
class TestOsvClient:
    """Verify OsvClient HTTP behavior for success and failure paths."""

    @respx.mock
    async def test_successful_query_returns_vulns(self) -> None:
        respx.post(f"{OSV_API_BASE_URL}/query").mock(
            return_value=httpx.Response(200, json=SAMPLE_VULN_RESPONSE)
        )
        client = _make_client()
        result = await client.fetch(name="example-package", ecosystem="PyPI")
        assert result is not None
        assert len(result["vulns"]) == 1
        assert result["vulns"][0]["id"] == "GHSA-1234-5678-abcd"

    @respx.mock
    async def test_empty_vulns_response(self) -> None:
        respx.post(f"{OSV_API_BASE_URL}/query").mock(
            return_value=httpx.Response(200, json=EMPTY_RESPONSE)
        )
        client = _make_client()
        result = await client.fetch(name="safe-package", ecosystem="npm")
        assert result is not None
        assert result["vulns"] == []

    @respx.mock
    async def test_http_error_returns_none(self) -> None:
        respx.post(f"{OSV_API_BASE_URL}/query").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        client = _make_client()
        result = await client.fetch(name="pkg", ecosystem="PyPI")
        assert result is None

    @respx.mock
    async def test_network_error_returns_none(self) -> None:
        respx.post(f"{OSV_API_BASE_URL}/query").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        client = _make_client()
        result = await client.fetch(name="pkg", ecosystem="PyPI")
        assert result is None

    @respx.mock
    async def test_missing_name_returns_none(self) -> None:
        client = _make_client()
        result = await client.fetch(ecosystem="PyPI")
        assert result is None

    @respx.mock
    async def test_missing_ecosystem_returns_none(self) -> None:
        client = _make_client()
        result = await client.fetch(name="pkg")
        assert result is None

    @respx.mock
    async def test_sends_version_when_provided(self) -> None:
        route = respx.post(f"{OSV_API_BASE_URL}/query").mock(
            return_value=httpx.Response(200, json=EMPTY_RESPONSE)
        )
        client = _make_client()
        await client.fetch(name="pkg", ecosystem="PyPI", version="1.2.3")
        assert route.called
        request_body = route.calls[0].request.content.decode()
        assert "1.2.3" in request_body
