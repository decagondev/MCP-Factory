"""Code quality analyzer.

Performs heuristic checks for common code-quality issues:
excessive file size, long lines, deep nesting, and functions
with too many parameters.  Language-agnostic where possible,
with language-specific parameter-detection for Python, JS/TS,
Java, and Go.
"""

from __future__ import annotations

import re

from mcp_factory.services.code_guardian.analyzers import BaseAnalyzer
from mcp_factory.services.code_guardian.config import (
    FILE_SIZE_ERROR_LINES,
    FILE_SIZE_WARN_LINES,
    LINE_LENGTH_LIMIT,
    MAX_FUNCTION_PARAMS,
    MAX_NESTING_DEPTH,
)
from mcp_factory.services.code_guardian.models import Finding, ScannedFile

_FUNCTION_SIGNATURES: list[tuple[re.Pattern[str], set[str]]] = [
    (
        re.compile(r"def\s+\w+\s*\(([^)]*)\)"),
        {"python"},
    ),
    (
        re.compile(r"(?:function|async\s+function)\s+\w+\s*\(([^)]*)\)"),
        {"javascript", "typescript"},
    ),
    (
        re.compile(r"(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>"),
        {"javascript", "typescript"},
    ),
    (
        re.compile(
            r"(?:public|private|protected|static|\s)*"
            r"(?:\w+(?:<[^>]+>)?)\s+\w+\s*\(([^)]*)\)"
        ),
        {"java", "csharp"},
    ),
    (
        re.compile(r"func\s+(?:\([^)]*\)\s+)?\w+\s*\(([^)]*)\)"),
        {"go"},
    ),
    (
        re.compile(r"fn\s+\w+\s*\(([^)]*)\)"),
        {"rust"},
    ),
]
"""(pattern_matching_param_list, applicable_languages) tuples."""

_NESTING_OPENERS = re.compile(r"[\{]")
_NESTING_CLOSERS = re.compile(r"[\}]")

_INDENT_LANGUAGES = {"python"}


class CodeQualityAnalyzer(BaseAnalyzer):
    """Checks file size, line length, nesting depth, and parameter count.

    Produces ``medium`` and ``low`` severity findings depending on
    the threshold exceeded.
    """

    @property
    def name(self) -> str:
        """Returns ``"code-quality-analyzer"``."""
        return "code-quality-analyzer"

    @property
    def category(self) -> str:
        """Returns ``"quality"``."""
        return "quality"

    async def analyze(self, files: list[ScannedFile]) -> list[Finding]:
        """Run quality checks on every file.

        Args:
            files: Pre-scanned source files.

        Returns:
            Aggregated quality findings.
        """
        findings: list[Finding] = []

        for scanned in files:
            findings.extend(self._check_file_size(scanned))
            findings.extend(self._check_long_lines(scanned))
            findings.extend(self._check_nesting_depth(scanned))
            findings.extend(self._check_function_params(scanned))

        return findings

    @staticmethod
    def _check_file_size(scanned: ScannedFile) -> list[Finding]:
        """Emit a finding when a file exceeds the line-count thresholds.

        Args:
            scanned: The file to check.

        Returns:
            Zero or one finding.
        """
        if scanned.line_count > FILE_SIZE_ERROR_LINES:
            return [
                Finding(
                    severity="medium",
                    category="quality",
                    rule="file-too-large",
                    message=f"File has {scanned.line_count} lines (>{FILE_SIZE_ERROR_LINES}); consider splitting",
                    file_path=scanned.path,
                )
            ]
        if scanned.line_count > FILE_SIZE_WARN_LINES:
            return [
                Finding(
                    severity="low",
                    category="quality",
                    rule="file-too-large",
                    message=f"File has {scanned.line_count} lines (>{FILE_SIZE_WARN_LINES}); consider splitting",
                    file_path=scanned.path,
                )
            ]
        return []

    @staticmethod
    def _check_long_lines(scanned: ScannedFile) -> list[Finding]:
        """Emit findings for lines exceeding the length limit.

        Args:
            scanned: The file to check.

        Returns:
            One finding per offending line.
        """
        findings: list[Finding] = []
        for line_num, line in enumerate(scanned.content.splitlines(), start=1):
            if len(line) > LINE_LENGTH_LIMIT:
                findings.append(
                    Finding(
                        severity="info",
                        category="quality",
                        rule="line-too-long",
                        message=f"Line is {len(line)} chars (>{LINE_LENGTH_LIMIT})",
                        file_path=scanned.path,
                        line_number=line_num,
                    )
                )
        return findings

    @staticmethod
    def _check_nesting_depth(scanned: ScannedFile) -> list[Finding]:
        """Detect excessive brace-nesting or indentation depth.

        For brace-delimited languages, counts ``{`` and ``}``.
        For Python, measures indentation level.

        Args:
            scanned: The file to check.

        Returns:
            One finding per line that exceeds the depth limit.
        """
        findings: list[Finding] = []

        if scanned.language in _INDENT_LANGUAGES:
            for line_num, line in enumerate(scanned.content.splitlines(), start=1):
                if not line.strip():
                    continue
                spaces = len(line) - len(line.lstrip())
                depth = spaces // 4
                if depth > MAX_NESTING_DEPTH:
                    findings.append(
                        Finding(
                            severity="medium",
                            category="quality",
                            rule="deep-nesting",
                            message=f"Nesting depth {depth} exceeds limit of {MAX_NESTING_DEPTH}",
                            file_path=scanned.path,
                            line_number=line_num,
                            snippet=line.strip()[:120],
                        )
                    )
        else:
            depth = 0
            for line_num, line in enumerate(scanned.content.splitlines(), start=1):
                depth += len(_NESTING_OPENERS.findall(line))
                depth -= len(_NESTING_CLOSERS.findall(line))
                depth = max(depth, 0)
                if depth > MAX_NESTING_DEPTH:
                    findings.append(
                        Finding(
                            severity="medium",
                            category="quality",
                            rule="deep-nesting",
                            message=f"Nesting depth {depth} exceeds limit of {MAX_NESTING_DEPTH}",
                            file_path=scanned.path,
                            line_number=line_num,
                            snippet=line.strip()[:120],
                        )
                    )

        return findings

    @staticmethod
    def _check_function_params(scanned: ScannedFile) -> list[Finding]:
        """Detect functions with too many parameters.

        Args:
            scanned: The file to check.

        Returns:
            One finding per function signature exceeding the limit.
        """
        findings: list[Finding] = []

        for line_num, line in enumerate(scanned.content.splitlines(), start=1):
            for pattern, languages in _FUNCTION_SIGNATURES:
                if scanned.language not in languages:
                    continue
                match = pattern.search(line)
                if not match:
                    continue
                params_str = match.group(1).strip()
                if not params_str:
                    continue
                param_count = len([p for p in params_str.split(",") if p.strip()])
                if param_count > MAX_FUNCTION_PARAMS:
                    findings.append(
                        Finding(
                            severity="low",
                            category="quality",
                            rule="too-many-params",
                            message=f"Function has {param_count} parameters (>{MAX_FUNCTION_PARAMS})",
                            file_path=scanned.path,
                            line_number=line_num,
                            snippet=line.strip()[:120],
                        )
                    )

        return findings
