"""Style and linting-heuristic analyzer.

Performs lightweight style checks inspired by PEP 8 (for Python) and
general best practices across languages: trailing whitespace,
superfluous/TODO comments, tab-vs-space mixing, and naming
convention hints.
"""

from __future__ import annotations

import re

from nasa_apod.services.code_guardian.analyzers import BaseAnalyzer
from nasa_apod.services.code_guardian.models import Finding, ScannedFile

_TODO_PATTERN = re.compile(r"(?i)\b(?:TODO|FIXME|HACK|XXX|TEMP)\b")
_TRAILING_WHITESPACE = re.compile(r"[ \t]+$")
_MIXED_INDENT = re.compile(r"^( +\t|\t+ )")

_PEP8_SNAKE_FUNC = re.compile(r"def\s+([a-z][a-zA-Z]+[A-Z][a-zA-Z]*)\s*\(")
_PEP8_CLASS_NAME = re.compile(r"class\s+([a-z_][a-z_0-9]*)\s*[\(:]")
_PEP8_CONSTANT_LOWER = re.compile(
    r"^([A-Z][A-Z_0-9]*)\s*=\s*"
)

_JS_SNAKE_FUNC = re.compile(
    r"(?:function\s+|(?:const|let|var)\s+)"
    r"([a-z]+_[a-z_]+)\s*(?:=\s*(?:async\s+)?(?:function|\()|\()"
)

_SUPERFLUOUS_COMMENT_PATTERNS: list[tuple[re.Pattern[str], set[str]]] = [
    (
        re.compile(r"^\s*#\s*(?:import|define|set|get|return|increment|decrement|initialize|init)\s", re.IGNORECASE),
        {"python"},
    ),
    (
        re.compile(r"^\s*//\s*(?:import|define|set|get|return|increment|decrement|initialize|init)\s", re.IGNORECASE),
        {"javascript", "typescript", "java", "go", "rust", "csharp", "c", "cpp"},
    ),
]
"""Patterns matching comments that simply narrate what the next line does."""


class StyleAnalyzer(BaseAnalyzer):
    """Detects style issues, linting hints, and superfluous comments.

    Checks trailing whitespace, TODO/FIXME markers, mixed indentation,
    PEP 8 naming for Python, camelCase conventions for JS/TS, and
    comments that just narrate code.
    """

    @property
    def name(self) -> str:
        """Returns ``"style-analyzer"``."""
        return "style-analyzer"

    @property
    def category(self) -> str:
        """Returns ``"style"``."""
        return "style"

    async def analyze(self, files: list[ScannedFile]) -> list[Finding]:
        """Run style checks on every file.

        Args:
            files: Pre-scanned source files.

        Returns:
            Aggregated style findings.
        """
        findings: list[Finding] = []

        for scanned in files:
            findings.extend(self._check_trailing_whitespace(scanned))
            findings.extend(self._check_todo_comments(scanned))
            findings.extend(self._check_mixed_indentation(scanned))
            findings.extend(self._check_superfluous_comments(scanned))

            if scanned.language == "python":
                findings.extend(self._check_pep8_naming(scanned))

            if scanned.language in {"javascript", "typescript"}:
                findings.extend(self._check_js_naming(scanned))

        return findings

    @staticmethod
    def _check_trailing_whitespace(scanned: ScannedFile) -> list[Finding]:
        """Detect trailing whitespace on non-empty lines.

        Args:
            scanned: The file to check.

        Returns:
            One finding per offending line.
        """
        findings: list[Finding] = []
        for line_num, line in enumerate(scanned.content.splitlines(), start=1):
            if _TRAILING_WHITESPACE.search(line) and line.strip():
                findings.append(
                    Finding(
                        severity="info",
                        category="style",
                        rule="trailing-whitespace",
                        message="Trailing whitespace detected",
                        file_path=scanned.path,
                        line_number=line_num,
                    )
                )
        return findings

    @staticmethod
    def _check_todo_comments(scanned: ScannedFile) -> list[Finding]:
        """Flag TODO, FIXME, HACK, XXX, and TEMP markers.

        Args:
            scanned: The file to check.

        Returns:
            One finding per marker.
        """
        findings: list[Finding] = []
        for line_num, line in enumerate(scanned.content.splitlines(), start=1):
            if _TODO_PATTERN.search(line):
                findings.append(
                    Finding(
                        severity="info",
                        category="style",
                        rule="todo-comment",
                        message="TODO/FIXME/HACK comment found",
                        file_path=scanned.path,
                        line_number=line_num,
                        snippet=line.strip()[:120],
                    )
                )
        return findings

    @staticmethod
    def _check_mixed_indentation(scanned: ScannedFile) -> list[Finding]:
        """Detect lines mixing tabs and spaces in indentation.

        Args:
            scanned: The file to check.

        Returns:
            One finding per offending line.
        """
        findings: list[Finding] = []
        for line_num, line in enumerate(scanned.content.splitlines(), start=1):
            if _MIXED_INDENT.match(line):
                findings.append(
                    Finding(
                        severity="low",
                        category="style",
                        rule="mixed-indentation",
                        message="Mixed tabs and spaces in indentation",
                        file_path=scanned.path,
                        line_number=line_num,
                    )
                )
        return findings

    @staticmethod
    def _check_superfluous_comments(scanned: ScannedFile) -> list[Finding]:
        """Flag comments that simply narrate the code.

        Args:
            scanned: The file to check.

        Returns:
            One finding per superfluous comment.
        """
        findings: list[Finding] = []
        for line_num, line in enumerate(scanned.content.splitlines(), start=1):
            for pattern, languages in _SUPERFLUOUS_COMMENT_PATTERNS:
                if scanned.language not in languages:
                    continue
                if pattern.match(line):
                    findings.append(
                        Finding(
                            severity="info",
                            category="style",
                            rule="superfluous-comment",
                            message="Comment appears to narrate code -- consider removing",
                            file_path=scanned.path,
                            line_number=line_num,
                            snippet=line.strip()[:120],
                        )
                    )
        return findings

    @staticmethod
    def _check_pep8_naming(scanned: ScannedFile) -> list[Finding]:
        """Check Python naming conventions (PEP 8).

        Flags camelCase function names and lowercase class names.

        Args:
            scanned: The file to check.

        Returns:
            Findings for naming violations.
        """
        findings: list[Finding] = []
        for line_num, line in enumerate(scanned.content.splitlines(), start=1):
            func_match = _PEP8_SNAKE_FUNC.search(line)
            if func_match:
                findings.append(
                    Finding(
                        severity="low",
                        category="style",
                        rule="pep8-naming",
                        message=f"Function '{func_match.group(1)}' uses camelCase; PEP 8 prefers snake_case",
                        file_path=scanned.path,
                        line_number=line_num,
                        snippet=line.strip()[:120],
                    )
                )

            class_match = _PEP8_CLASS_NAME.search(line)
            if class_match:
                findings.append(
                    Finding(
                        severity="low",
                        category="style",
                        rule="pep8-naming",
                        message=f"Class '{class_match.group(1)}' should use CapitalizedWords (PEP 8)",
                        file_path=scanned.path,
                        line_number=line_num,
                        snippet=line.strip()[:120],
                    )
                )

        return findings

    @staticmethod
    def _check_js_naming(scanned: ScannedFile) -> list[Finding]:
        """Check JS/TS naming conventions.

        Flags snake_case function/variable names (JS convention is
        camelCase).

        Args:
            scanned: The file to check.

        Returns:
            Findings for naming violations.
        """
        findings: list[Finding] = []
        for line_num, line in enumerate(scanned.content.splitlines(), start=1):
            match = _JS_SNAKE_FUNC.search(line)
            if match:
                findings.append(
                    Finding(
                        severity="info",
                        category="style",
                        rule="js-naming-convention",
                        message=f"'{match.group(1)}' uses snake_case; JS convention prefers camelCase",
                        file_path=scanned.path,
                        line_number=line_num,
                        snippet=line.strip()[:120],
                    )
                )
        return findings
