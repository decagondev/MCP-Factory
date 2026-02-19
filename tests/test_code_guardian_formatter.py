"""Tests for mcp_factory.services.code_guardian.formatter."""

import pytest

from mcp_factory.services.code_guardian.formatter import CodeGuardianFormatter
from mcp_factory.services.code_guardian.models import Finding, ScanResult


def _sample_result() -> ScanResult:
    """Build a ScanResult with mixed-severity findings for testing."""
    return ScanResult(
        findings=[
            Finding(
                severity="critical",
                category="security",
                rule="exposed-api-key",
                message="AWS key found",
                file_path="config.py",
                line_number=10,
                snippet="AWS_KEY='AKIA...'",
            ),
            Finding(
                severity="low",
                category="quality",
                rule="console-log",
                message="console.log found",
                file_path="app.js",
                line_number=5,
            ),
            Finding(
                severity="medium",
                category="style",
                rule="long-line",
                message="Line exceeds 120 chars",
                file_path="utils.py",
                line_number=88,
            ),
        ],
        files_scanned=12,
        analyzers_run=["secret-scanner", "style-analyzer"],
    )


class TestCodeGuardianFormatter:
    """Verify Markdown report generation."""

    def test_format_includes_summary(self) -> None:
        fmt = CodeGuardianFormatter()
        data = fmt.scan_result_to_dict(_sample_result())
        report = fmt.format(data)
        assert "Code Guardian Scan Report" in report
        assert "Files scanned:** 12" in report
        assert "Total findings:** 3" in report

    def test_format_groups_by_severity(self) -> None:
        fmt = CodeGuardianFormatter()
        data = fmt.scan_result_to_dict(_sample_result())
        report = fmt.format(data)
        assert "CRITICAL" in report
        assert "MEDIUM" in report
        assert "LOW" in report

    def test_format_includes_finding_details(self) -> None:
        fmt = CodeGuardianFormatter()
        data = fmt.scan_result_to_dict(_sample_result())
        report = fmt.format(data)
        assert "exposed-api-key" in report
        assert "AWS key found" in report
        assert "config.py:10" in report

    def test_format_includes_snippet_when_present(self) -> None:
        fmt = CodeGuardianFormatter()
        data = fmt.scan_result_to_dict(_sample_result())
        report = fmt.format(data)
        assert "AKIA" in report

    def test_format_with_header(self) -> None:
        fmt = CodeGuardianFormatter()
        data = fmt.scan_result_to_dict(_sample_result())
        report = fmt.format(data, header="**Custom Header**")
        assert report.startswith("**Custom Header**")

    def test_format_empty_result(self) -> None:
        fmt = CodeGuardianFormatter()
        result = ScanResult(findings=[], files_scanned=5, analyzers_run=["a"])
        data = fmt.scan_result_to_dict(result)
        report = fmt.format(data)
        assert "No issues found" in report
        assert "Files scanned:** 5" in report

    def test_format_scan_result_convenience(self) -> None:
        fmt = CodeGuardianFormatter()
        report = fmt.format_scan_result(_sample_result())
        assert "Code Guardian Scan Report" in report

    def test_scan_result_to_dict_structure(self) -> None:
        fmt = CodeGuardianFormatter()
        data = fmt.scan_result_to_dict(_sample_result())
        assert "findings" in data
        assert "files_scanned" in data
        assert "analyzers_run" in data
        assert isinstance(data["findings"], list)
        assert data["files_scanned"] == 12

    def test_format_includes_analyzers_run(self) -> None:
        fmt = CodeGuardianFormatter()
        data = fmt.scan_result_to_dict(_sample_result())
        report = fmt.format(data)
        assert "secret-scanner" in report
        assert "style-analyzer" in report
