"""Tests for mcp_factory.services.code_guardian.models."""

import pytest

from mcp_factory.services.code_guardian.models import (
    SEVERITY_ORDER,
    Finding,
    ScanResult,
    ScannedFile,
)


class TestScannedFile:
    """Verify ScannedFile immutability and field access."""

    def test_fields_are_accessible(self) -> None:
        sf = ScannedFile(path="app.py", content="x = 1\n", language="python", line_count=1)
        assert sf.path == "app.py"
        assert sf.language == "python"
        assert sf.line_count == 1

    def test_frozen_prevents_mutation(self) -> None:
        sf = ScannedFile(path="a.py", content="", language="python", line_count=0)
        with pytest.raises(AttributeError):
            sf.path = "b.py"  # type: ignore[misc]


class TestFinding:
    """Verify Finding immutability, defaults, and field access."""

    def test_required_fields(self) -> None:
        f = Finding(
            severity="high",
            category="security",
            rule="exposed-key",
            message="Found API key",
            file_path="config.py",
        )
        assert f.severity == "high"
        assert f.line_number is None
        assert f.snippet is None

    def test_optional_fields(self) -> None:
        f = Finding(
            severity="low",
            category="quality",
            rule="debug-stmt",
            message="console.log found",
            file_path="index.js",
            line_number=42,
            snippet="console.log('debug')",
        )
        assert f.line_number == 42
        assert f.snippet == "console.log('debug')"

    def test_frozen_prevents_mutation(self) -> None:
        f = Finding(
            severity="info",
            category="style",
            rule="trailing-ws",
            message="Trailing whitespace",
            file_path="main.py",
        )
        with pytest.raises(AttributeError):
            f.severity = "critical"  # type: ignore[misc]


class TestScanResult:
    """Verify ScanResult aggregation helpers."""

    def _make_findings(self) -> list[Finding]:
        return [
            Finding(severity="low", category="quality", rule="r1", message="m1", file_path="a.py"),
            Finding(severity="critical", category="security", rule="r2", message="m2", file_path="b.py"),
            Finding(severity="medium", category="style", rule="r3", message="m3", file_path="c.py"),
            Finding(severity="critical", category="security", rule="r4", message="m4", file_path="d.py"),
            Finding(severity="high", category="security", rule="r5", message="m5", file_path="e.py"),
        ]

    def test_default_empty(self) -> None:
        result = ScanResult()
        assert result.findings == []
        assert result.files_scanned == 0
        assert result.analyzers_run == []

    def test_sorted_findings_orders_by_severity(self) -> None:
        result = ScanResult(findings=self._make_findings(), files_scanned=5, analyzers_run=["a"])
        sorted_f = result.sorted_findings()
        severities = [f.severity for f in sorted_f]
        assert severities == ["critical", "critical", "high", "medium", "low"]

    def test_counts_by_severity(self) -> None:
        result = ScanResult(findings=self._make_findings(), files_scanned=5, analyzers_run=["a"])
        counts = result.counts_by_severity()
        assert counts == {"critical": 2, "high": 1, "medium": 1, "low": 1}


class TestSeverityOrder:
    """Verify the severity ordering map."""

    def test_critical_is_most_severe(self) -> None:
        assert SEVERITY_ORDER["critical"] < SEVERITY_ORDER["info"]

    def test_all_levels_present(self) -> None:
        assert set(SEVERITY_ORDER.keys()) == {"critical", "high", "medium", "low", "info"}
