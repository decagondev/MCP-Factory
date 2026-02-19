"""Debug statement analyzer.

Detects leftover debug/logging statements that should be removed
before code reaches production: ``console.log`` (JS/TS),
``print()`` (Python), ``println``/``printf`` (Java/Go/C),
``cout``/``cerr`` (C++), ``puts``/``p``/``pp`` (Ruby), and
``dbg!`` (Rust).
"""

from __future__ import annotations

import re

from nasa_apod.services.code_guardian.analyzers import BaseAnalyzer
from nasa_apod.services.code_guardian.models import Finding, ScannedFile

_DEBUG_PATTERNS: list[tuple[re.Pattern[str], str, set[str]]] = [
    (
        re.compile(r"(?<![.\w])console\s*\.\s*(?:log|warn|error|debug|info|trace|dir|table)\s*\("),
        "console.{method}() statement found",
        {"javascript", "typescript"},
    ),
    (
        re.compile(r"(?<![.\w])print\s*\("),
        "print() statement found",
        {"python"},
    ),
    (
        re.compile(r"(?<![.\w])(?:System\.out\.println|System\.err\.println|System\.out\.printf)\s*\("),
        "System.out/err print statement found",
        {"java"},
    ),
    (
        re.compile(r"(?<![.\w])fmt\.Print(?:ln|f)?\s*\("),
        "fmt.Print statement found",
        {"go"},
    ),
    (
        re.compile(r"(?<![.\w])printf\s*\("),
        "printf() statement found",
        {"c", "cpp"},
    ),
    (
        re.compile(r"(?<![.\w])(?:std::cout|std::cerr|cout|cerr)\s*<<"),
        "cout/cerr output stream found",
        {"cpp"},
    ),
    (
        re.compile(r"(?<![.\w])(?:puts|pp?)\s+[\"']"),
        "puts/p/pp debug output found",
        {"ruby"},
    ),
    (
        re.compile(r"(?<![.\w])dbg!\s*\("),
        "dbg!() macro found",
        {"rust"},
    ),
    (
        re.compile(r"(?<![.\w])var_dump\s*\("),
        "var_dump() statement found",
        {"php"},
    ),
    (
        re.compile(r"(?<![.\w])print_r\s*\("),
        "print_r() statement found",
        {"php"},
    ),
    (
        re.compile(r"(?<![.\w])error_log\s*\("),
        "error_log() statement found",
        {"php"},
    ),
]
"""(pattern, message_template, applicable_languages) tuples."""


class DebugStatementAnalyzer(BaseAnalyzer):
    """Detects leftover debug/print statements across many languages.

    Produces ``low``-severity findings for each occurrence so they can
    be cleaned up before shipping.
    """

    @property
    def name(self) -> str:
        """Returns ``"debug-statement-analyzer"``."""
        return "debug-statement-analyzer"

    @property
    def category(self) -> str:
        """Returns ``"quality"``."""
        return "quality"

    async def analyze(self, files: list[ScannedFile]) -> list[Finding]:
        """Scan files for debug/print statements.

        Args:
            files: Pre-scanned source files.

        Returns:
            Findings for every detected debug statement.
        """
        findings: list[Finding] = []

        for scanned in files:
            lines = scanned.content.splitlines()
            for line_num, line in enumerate(lines, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith(("#", "//", "/*", "*")):
                    continue
                for pattern, message, languages in _DEBUG_PATTERNS:
                    if scanned.language not in languages:
                        continue
                    if pattern.search(line):
                        findings.append(
                            Finding(
                                severity="low",
                                category="quality",
                                rule="debug-statement",
                                message=message,
                                file_path=scanned.path,
                                line_number=line_num,
                                snippet=stripped[:120],
                            )
                        )

        return findings
