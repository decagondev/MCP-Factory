"""Tests for mcp_factory.services.registry.ServiceRegistry."""

from unittest.mock import MagicMock

import pytest

from mcp_factory.services.registry import ServiceRegistry


class _StubPlugin:
    """Minimal plugin that records whether register was called."""

    def __init__(self) -> None:
        self.registered = False
        self.received_mcp = None

    def register(self, mcp) -> None:
        self.registered = True
        self.received_mcp = mcp


class TestServiceRegistry:
    """Verify the ServiceRegistry factory behavior."""

    def test_starts_empty(self) -> None:
        registry = ServiceRegistry()
        assert registry.plugins == []

    def test_add_stores_plugin(self) -> None:
        registry = ServiceRegistry()
        plugin = _StubPlugin()
        registry.add(plugin)
        assert len(registry.plugins) == 1
        assert registry.plugins[0] is plugin

    def test_add_multiple_plugins(self) -> None:
        registry = ServiceRegistry()
        p1, p2 = _StubPlugin(), _StubPlugin()
        registry.add(p1)
        registry.add(p2)
        assert len(registry.plugins) == 2

    def test_apply_all_calls_register_on_each_plugin(self) -> None:
        registry = ServiceRegistry()
        p1, p2 = _StubPlugin(), _StubPlugin()
        registry.add(p1)
        registry.add(p2)

        mock_mcp = MagicMock()
        registry.apply_all(mock_mcp)

        assert p1.registered is True
        assert p2.registered is True
        assert p1.received_mcp is mock_mcp
        assert p2.received_mcp is mock_mcp

    def test_apply_all_preserves_order(self) -> None:
        registry = ServiceRegistry()
        call_order: list[str] = []

        class OrderedPlugin:
            def __init__(self, name: str) -> None:
                self._name = name

            def register(self, mcp) -> None:
                call_order.append(self._name)

        registry.add(OrderedPlugin("first"))
        registry.add(OrderedPlugin("second"))
        registry.apply_all(MagicMock())

        assert call_order == ["first", "second"]

    def test_plugins_returns_copy(self) -> None:
        registry = ServiceRegistry()
        plugin = _StubPlugin()
        registry.add(plugin)
        plugins_copy = registry.plugins
        plugins_copy.clear()
        assert len(registry.plugins) == 1
