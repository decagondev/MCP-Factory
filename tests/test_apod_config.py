"""Tests for mcp_factory.services.apod.config."""

from datetime import datetime


class TestApodConfigConstants:
    """Verify APOD-specific configuration constants are set to expected values."""

    def test_api_base_url(self) -> None:
        from mcp_factory.services.apod.config import NASA_APOD_BASE_URL

        assert NASA_APOD_BASE_URL == "https://api.nasa.gov/planetary/apod"

    def test_first_apod_date(self) -> None:
        from mcp_factory.services.apod.config import FIRST_APOD_DATE

        assert FIRST_APOD_DATE == datetime(1995, 6, 16)

    def test_date_format(self) -> None:
        from mcp_factory.services.apod.config import DATE_FORMAT

        assert DATE_FORMAT == "%Y-%m-%d"

    def test_request_timeout_is_positive(self) -> None:
        from mcp_factory.services.apod.config import REQUEST_TIMEOUT_SECONDS

        assert REQUEST_TIMEOUT_SECONDS > 0


class TestApiKeyLoading:
    """Verify API key falls back to DEMO_KEY or reads from env."""

    def test_defaults_to_demo_key_when_env_unset(self, monkeypatch) -> None:
        monkeypatch.delenv("NASA_API_KEY", raising=False)

        import importlib
        import mcp_factory.services.apod.config as cfg

        importlib.reload(cfg)
        assert cfg.NASA_API_KEY == "DEMO_KEY"

    def test_reads_from_environment_variable(self, monkeypatch) -> None:
        monkeypatch.setenv("NASA_API_KEY", "my-real-key-123")

        import importlib
        import mcp_factory.services.apod.config as cfg

        importlib.reload(cfg)
        assert cfg.NASA_API_KEY == "my-real-key-123"
