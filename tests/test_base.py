"""Tests for nasa_apod.services.base ABC contracts."""

from typing import Any

import pytest

from nasa_apod.services.base import BaseAPIClient, BaseFormatter


class ConcreteClient(BaseAPIClient):
    """Minimal concrete implementation for testing the ABC."""

    async def fetch(self, **params: str) -> dict[str, Any] | None:
        return {"mock": True, **params}


class ConcreteFormatter(BaseFormatter):
    """Minimal concrete implementation for testing the ABC."""

    def format(self, data: dict[str, Any], **kwargs: Any) -> str:
        return f"formatted: {data}"


class TestBaseAPIClient:
    """Verify the BaseAPIClient ABC contract and constructor."""

    def test_constructor_stores_attributes(self) -> None:
        client = ConcreteClient(
            base_url="https://example.com/api",
            api_key="test-key",
            timeout=15.0,
        )
        assert client.base_url == "https://example.com/api"
        assert client.api_key == "test-key"
        assert client.timeout == 15.0

    def test_default_timeout(self) -> None:
        client = ConcreteClient(base_url="https://example.com", api_key="k")
        assert client.timeout == 30.0

    def test_cannot_instantiate_abstract_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseAPIClient(base_url="x", api_key="y")  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_concrete_fetch_returns_data(self) -> None:
        client = ConcreteClient(base_url="https://example.com", api_key="k")
        result = await client.fetch(date="2024-01-01")
        assert result is not None
        assert result["date"] == "2024-01-01"


class TestBaseFormatter:
    """Verify the BaseFormatter ABC contract."""

    def test_cannot_instantiate_abstract_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseFormatter()  # type: ignore[abstract]

    def test_concrete_format_returns_string(self) -> None:
        formatter = ConcreteFormatter()
        result = formatter.format({"key": "value"})
        assert isinstance(result, str)
        assert "key" in result
