"""Data models for the Code Guardian service.

Defines the value objects used throughout the analysis pipeline:

- ``ScannedFile`` -- a single source file read from disk
- ``Finding`` -- one issue discovered by an analyzer
- ``ScanResult`` -- aggregated output from one or more analyzer passes
"""

from __future__ import annotations

from dataclasses import dataclass, field


SEVERITY_ORDER: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}
"""Ordering map so findings can be sorted most-severe-first."""


@dataclass(frozen=True)
class ScannedFile:
    """A single source file read from disk and ready for analysis.

    Attributes:
        path: Absolute or relative path to the file.
        content: Full text content of the file.
        language: Detected programming language (e.g. ``"python"``).
        line_count: Total number of lines in the file.
    """

    path: str
    content: str
    language: str
    line_count: int


@dataclass(frozen=True)
class Finding:
    """A single issue discovered by an analyzer.

    Attributes:
        severity: One of ``"critical"``, ``"high"``, ``"medium"``,
                  ``"low"``, or ``"info"``.
        category: Broad classification such as ``"security"``,
                  ``"quality"``, ``"style"``, or ``"vulnerability"``.
        rule: Machine-readable rule identifier
              (e.g. ``"exposed-api-key"``).
        message: Human-readable description of the issue.
        file_path: Path to the file where the issue was found.
        line_number: 1-based line number, or ``None`` for file-level
                     findings.
        snippet: Optional source code excerpt for context.
    """

    severity: str
    category: str
    rule: str
    message: str
    file_path: str
    line_number: int | None = None
    snippet: str | None = None


@dataclass
class ScanResult:
    """Aggregated output from one or more analyzer passes.

    Attributes:
        findings: Every issue discovered during the scan.
        files_scanned: Number of source files that were analyzed.
        analyzers_run: Names of the analyzers that participated.
    """

    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    analyzers_run: list[str] = field(default_factory=list)

    def sorted_findings(self) -> list[Finding]:
        """Return findings ordered by severity (most severe first).

        Returns:
            A new list of :class:`Finding` sorted by the
            ``SEVERITY_ORDER`` mapping.
        """
        return sorted(
            self.findings,
            key=lambda f: SEVERITY_ORDER.get(f.severity, 99),
        )

    def counts_by_severity(self) -> dict[str, int]:
        """Tally findings grouped by severity level.

        Returns:
            A dictionary mapping severity strings to their count.
        """
        counts: dict[str, int] = {}
        for finding in self.findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return counts
