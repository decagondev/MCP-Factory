"""Code Guardian response formatter extending BaseFormatter.

Converts :class:`~nasa_apod.services.code_guardian.models.ScanResult`
data into the Markdown report string returned by every Code Guardian
MCP tool.
"""

from __future__ import annotations

from typing import Any

from nasa_apod.services.base import BaseFormatter
from nasa_apod.services.code_guardian.models import (
    SEVERITY_ORDER,
    Finding,
    ScanResult,
)


class CodeGuardianFormatter(BaseFormatter):
    """Renders scan results as a structured Markdown report.

    Extends :class:`~nasa_apod.services.base.BaseFormatter` with
    Code-Guardian-specific logic: severity grouping, summary
    statistics, and per-finding detail blocks.
    """

    _SEVERITY_EMOJI: dict[str, str] = {
        "critical": "\U0001f6d1",
        "high": "\U0001f534",
        "medium": "\U0001f7e0",
        "low": "\U0001f7e1",
        "info": "\U0001f535",
    }

    def format(self, data: dict[str, Any], **kwargs: Any) -> str:
        """Format a scan-result dictionary into a Markdown report.

        Args:
            data: A dictionary produced by
                  :meth:`_scan_result_to_dict`.  Must contain keys
                  ``findings``, ``files_scanned``, and
                  ``analyzers_run``.
            **kwargs: Optional ``header`` string prepended to the
                      report.

        Returns:
            A Markdown-formatted report string.
        """
        header: str | None = kwargs.get("header")
        parts: list[str] = []

        if header:
            parts.append(header)
            parts.append("")

        findings: list[dict[str, Any]] = data.get("findings", [])
        files_scanned: int = data.get("files_scanned", 0)
        analyzers_run: list[str] = data.get("analyzers_run", [])

        parts.append(self._format_summary(findings, files_scanned, analyzers_run))
        parts.append("")

        if not findings:
            parts.append("No issues found -- your code looks clean!")
            return "\n".join(parts)

        grouped = self._group_by_severity(findings)
        for severity in SEVERITY_ORDER:
            group = grouped.get(severity, [])
            if not group:
                continue
            emoji = self._SEVERITY_EMOJI.get(severity, "")
            parts.append(f"### {emoji} {severity.upper()} ({len(group)})")
            parts.append("")
            for finding in group:
                parts.append(self._format_finding(finding))
            parts.append("")

        return "\n".join(parts)

    def format_scan_result(self, result: ScanResult, **kwargs: Any) -> str:
        """Convenience wrapper accepting a :class:`ScanResult` directly.

        Args:
            result: The aggregated scan result to format.
            **kwargs: Forwarded to :meth:`format`.

        Returns:
            Markdown report string.
        """
        return self.format(self.scan_result_to_dict(result), **kwargs)

    @staticmethod
    def scan_result_to_dict(result: ScanResult) -> dict[str, Any]:
        """Serialise a :class:`ScanResult` into a plain dictionary.

        Args:
            result: The scan result to convert.

        Returns:
            Dictionary suitable for :meth:`format`.
        """
        return {
            "findings": [
                {
                    "severity": f.severity,
                    "category": f.category,
                    "rule": f.rule,
                    "message": f.message,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "snippet": f.snippet,
                }
                for f in result.sorted_findings()
            ],
            "files_scanned": result.files_scanned,
            "analyzers_run": result.analyzers_run,
        }

    def _format_summary(
        self,
        findings: list[dict[str, Any]],
        files_scanned: int,
        analyzers_run: list[str],
    ) -> str:
        """Build the summary header block.

        Args:
            findings: Serialised finding dictionaries.
            files_scanned: Total files analysed.
            analyzers_run: Names of participating analyzers.

        Returns:
            Markdown summary section.
        """
        parts = [
            "## Code Guardian Scan Report",
            "",
            f"**Files scanned:** {files_scanned}",
            f"**Analyzers run:** {', '.join(analyzers_run) if analyzers_run else 'none'}",
            f"**Total findings:** {len(findings)}",
        ]

        counts: dict[str, int] = {}
        for f in findings:
            sev = f["severity"]
            counts[sev] = counts.get(sev, 0) + 1

        if counts:
            breakdown = " | ".join(
                f"{self._SEVERITY_EMOJI.get(s, '')} {s}: {counts[s]}"
                for s in SEVERITY_ORDER
                if s in counts
            )
            parts.append(f"**Breakdown:** {breakdown}")

        return "\n".join(parts)

    @staticmethod
    def _group_by_severity(
        findings: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Partition findings into severity buckets.

        Args:
            findings: Flat list of finding dictionaries.

        Returns:
            Dictionary keyed by severity with lists of findings.
        """
        groups: dict[str, list[dict[str, Any]]] = {}
        for f in findings:
            groups.setdefault(f["severity"], []).append(f)
        return groups

    @staticmethod
    def _format_finding(finding: dict[str, Any]) -> str:
        """Render a single finding as a Markdown list item.

        Args:
            finding: Serialised finding dictionary.

        Returns:
            Formatted string for one finding.
        """
        location = finding["file_path"]
        if finding.get("line_number"):
            location += f":{finding['line_number']}"

        line = f"- **[{finding['rule']}]** {finding['message']} (`{location}`)"

        if finding.get("snippet"):
            line += f"\n  ```\n  {finding['snippet']}\n  ```"

        return line
