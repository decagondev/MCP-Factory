"""OWASP-inspired security antipattern analyzer.

Detects common security mistakes across multiple languages:
SQL injection vectors, XSS sinks, ``eval()`` usage, insecure
cryptographic primitives, path-traversal patterns, and insecure
deserialization.
"""

from __future__ import annotations

import re

from mcp_factory.services.code_guardian.analyzers import BaseAnalyzer
from mcp_factory.services.code_guardian.models import Finding, ScannedFile

_SECURITY_PATTERNS: list[tuple[str, str, re.Pattern[str], str, set[str]]] = [
    (
        "sql-injection",
        "high",
        re.compile(
            r"(?i)(?:execute|exec|query|cursor\.execute)\s*\("
            r"[^)]*(?:\+|%|\.format|f[\"'])"
        ),
        "Possible SQL injection via string concatenation or formatting",
        {"python", "javascript", "typescript", "java", "ruby", "php", "csharp", "go"},
    ),
    (
        "sql-injection-fstring",
        "high",
        re.compile(r"""f[\"'](?:[^\"']*?)(?:SELECT|INSERT|UPDATE|DELETE|DROP)""", re.IGNORECASE),
        "Possible SQL injection via f-string",
        {"python"},
    ),
    (
        "xss-innerhtml",
        "high",
        re.compile(r"\.innerHTML\s*="),
        "Direct innerHTML assignment is an XSS risk",
        {"javascript", "typescript", "html"},
    ),
    (
        "xss-dangerously-set",
        "high",
        re.compile(r"dangerouslySetInnerHTML"),
        "dangerouslySetInnerHTML usage detected -- ensure input is sanitised",
        {"javascript", "typescript"},
    ),
    (
        "xss-document-write",
        "medium",
        re.compile(r"document\.write\s*\("),
        "document.write is an XSS risk when used with untrusted data",
        {"javascript", "typescript", "html"},
    ),
    (
        "eval-usage",
        "high",
        re.compile(r"(?<![.\w])eval\s*\("),
        "eval() executes arbitrary code and should be avoided",
        {"python", "javascript", "typescript", "ruby", "php"},
    ),
    (
        "insecure-hash-md5",
        "medium",
        re.compile(r"(?i)(?:md5|MD5)\s*[\.(]"),
        "MD5 is cryptographically broken -- use SHA-256 or better",
        {"python", "javascript", "typescript", "java", "go", "ruby", "php", "csharp"},
    ),
    (
        "insecure-hash-sha1",
        "medium",
        re.compile(r"(?i)(?:sha1|SHA1)\s*[\.(]"),
        "SHA-1 is deprecated for security -- use SHA-256 or better",
        {"python", "javascript", "typescript", "java", "go", "ruby", "php", "csharp"},
    ),
    (
        "path-traversal",
        "high",
        re.compile(r"""(?:open|readFile|readFileSync|include|require)\s*\([^)]*\.\./"""),
        "Possible path traversal via relative parent references",
        {"python", "javascript", "typescript", "ruby", "php"},
    ),
    (
        "insecure-deserialization",
        "high",
        re.compile(r"(?:pickle\.loads?|yaml\.load\s*\([^)]*\)(?!\s*,\s*Loader)|marshal\.loads?)"),
        "Insecure deserialization can lead to remote code execution",
        {"python"},
    ),
    (
        "insecure-random",
        "medium",
        re.compile(r"(?<![.\w])Math\.random\s*\("),
        "Math.random() is not cryptographically secure -- use crypto.getRandomValues()",
        {"javascript", "typescript"},
    ),
    (
        "hardcoded-ip",
        "low",
        re.compile(
            r"(?<![.\d])"
            r"(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|[01]?\d?\d)"
            r"(?![.\d])"
        ),
        "Hardcoded IP address detected -- prefer configuration or DNS",
        {"python", "javascript", "typescript", "java", "go", "ruby", "php",
         "csharp", "c", "cpp", "rust", "shell", "yaml", "json", "toml"},
    ),
    (
        "subprocess-shell-true",
        "high",
        re.compile(r"subprocess\.\w+\([^)]*shell\s*=\s*True"),
        "subprocess with shell=True is vulnerable to shell injection",
        {"python"},
    ),
    (
        "exec-usage",
        "high",
        re.compile(r"(?<![.\w])exec\s*\("),
        "exec() executes arbitrary code and should be avoided",
        {"python"},
    ),
]
"""(rule_id, severity, pattern, message, applicable_languages) tuples."""


class SecurityPatternAnalyzer(BaseAnalyzer):
    """Detects OWASP-inspired security antipatterns in source code.

    Each pattern is language-scoped so it only fires on files where
    the construct is actually meaningful.
    """

    @property
    def name(self) -> str:
        """Returns ``"security-pattern-analyzer"``."""
        return "security-pattern-analyzer"

    @property
    def category(self) -> str:
        """Returns ``"security"``."""
        return "security"

    async def analyze(self, files: list[ScannedFile]) -> list[Finding]:
        """Scan files for OWASP-style security antipatterns.

        Args:
            files: Pre-scanned source files.

        Returns:
            Findings for every detected antipattern.
        """
        findings: list[Finding] = []

        for scanned in files:
            lines = scanned.content.splitlines()
            for line_num, line in enumerate(lines, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                for rule_id, severity, pattern, message, languages in _SECURITY_PATTERNS:
                    if scanned.language not in languages:
                        continue
                    if pattern.search(line):
                        findings.append(
                            Finding(
                                severity=severity,
                                category="security",
                                rule=rule_id,
                                message=message,
                                file_path=scanned.path,
                                line_number=line_num,
                                snippet=stripped[:120],
                            )
                        )

        return findings
