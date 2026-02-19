"""Tests for nasa_apod.services.apod.client using respx to mock httpx."""

import httpx
import pytest
import respx

from nasa_apod.services.apod.client import ApodClient
from nasa_apod.services.apod.config import NASA_APOD_BASE_URL

SAMPLE_RESPONSE: dict = {
    "title": "Test Galaxy",
    "date": "2024-01-15",
    "explanation": "A beautiful galaxy captured by Hubble.",
    "media_type": "image",
    "url": "https://apod.nasa.gov/apod/image/2401/galaxy.jpg",
}


def _make_client() -> ApodClient:
    """Create an ApodClient wired to the real APOD base URL for testing."""
    return ApodClient(
        base_url=NASA_APOD_BASE_URL,
        api_key="DEMO_KEY",
        timeout=10.0,
    )


@pytest.mark.asyncio
class TestApodClient:
    """Verify ApodClient behavior for success and failure scenarios."""

    @respx.mock
    async def test_successful_fetch_returns_dict(self) -> None:
        respx.get(NASA_APOD_BASE_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        client = _make_client()
        result = await client.fetch()
        assert result is not None
        assert result["title"] == "Test Galaxy"

    @respx.mock
    async def test_fetch_with_date_sends_date_param(self) -> None:
        route = respx.get(NASA_APOD_BASE_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        client = _make_client()
        await client.fetch(date="2024-01-15")
        assert route.called
        assert "date" in str(route.calls[0].request.url)

    @respx.mock
    async def test_http_error_returns_none(self) -> None:
        respx.get(NASA_APOD_BASE_URL).mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        client = _make_client()
        result = await client.fetch()
        assert result is None

    @respx.mock
    async def test_network_error_returns_none(self) -> None:
        respx.get(NASA_APOD_BASE_URL).mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        client = _make_client()
        result = await client.fetch()
        assert result is None

    @respx.mock
    async def test_fetch_without_date_omits_date_param(self) -> None:
        route = respx.get(NASA_APOD_BASE_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        client = _make_client()
        await client.fetch()
        request_url = str(route.calls[0].request.url)
        assert "date=" not in request_url
