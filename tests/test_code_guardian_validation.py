"""Tests for mcp_factory.services.code_guardian.validation."""

import os
import tempfile

from mcp_factory.services.code_guardian.validation import validate_scan_path


class TestValidateScanPath:
    """Verify path validation logic for scan tool inputs."""

    def test_valid_directory_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            assert validate_scan_path(tmp) is None

    def test_empty_string_returns_error(self) -> None:
        result = validate_scan_path("")
        assert result is not None
        assert "empty" in result.lower()

    def test_whitespace_only_returns_error(self) -> None:
        result = validate_scan_path("   ")
        assert result is not None
        assert "empty" in result.lower()

    def test_nonexistent_path_returns_error(self) -> None:
        result = validate_scan_path("/tmp/nonexistent_path_12345")
        assert result is not None
        assert "does not exist" in result

    def test_file_path_returns_error(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            result = validate_scan_path(tmp.name)
            assert result is not None
            assert "not a directory" in result

    def test_tilde_expansion(self) -> None:
        home = os.path.expanduser("~")
        result = validate_scan_path("~")
        if os.path.isdir(home) and os.access(home, os.R_OK):
            assert result is None
