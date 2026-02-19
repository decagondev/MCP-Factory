"""Secret and credential detection analyzer.

Scans source files for patterns that typically indicate exposed
secrets: API keys, authentication tokens, private keys, connection
strings, and passwords in configuration.  Uses compiled regular
expressions for performance.
"""

from __future__ import annotations

import re

from nasa_apod.services.code_guardian.analyzers import BaseAnalyzer
from nasa_apod.services.code_guardian.models import Finding, ScannedFile

_SECRET_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "aws-access-key",
        re.compile(r"(?:^|[\"'\s=:])(?:AKIA[0-9A-Z]{16})(?:[\"'\s,;]|$)"),
        "Possible AWS access key ID detected",
    ),
    (
        "aws-secret-key",
        re.compile(
            r"(?i)(?:aws_secret_access_key|aws_secret_key|secret_key)"
            r"\s*[=:]\s*[\"']?[A-Za-z0-9/+=]{40}[\"']?"
        ),
        "Possible AWS secret access key detected",
    ),
    (
        "github-token",
        re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}"),
        "Possible GitHub personal access token detected",
    ),
    (
        "generic-api-key",
        re.compile(
            r"(?i)(?:api[_-]?key|apikey|api[_-]?secret|api[_-]?token)"
            r"\s*[=:]\s*[\"']?[A-Za-z0-9_\-]{20,}[\"']?"
        ),
        "Possible API key or secret in assignment",
    ),
    (
        "generic-secret",
        re.compile(
            r"(?i)(?:secret|password|passwd|pwd|token|auth[_-]?token|access[_-]?token)"
            r"\s*[=:]\s*[\"'][^\"']{8,}[\"']"
        ),
        "Possible hardcoded secret or password",
    ),
    (
        "private-key",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
        "Private key material detected",
    ),
    (
        "jwt-token",
        re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_\-]+"),
        "Possible JWT token detected",
    ),
    (
        "connection-string",
        re.compile(
            r"(?i)(?:mongodb|postgres|mysql|redis|amqp|mssql)"
            r"(?:ql)?://[^\s\"']{10,}"
        ),
        "Database or service connection string detected",
    ),
    (
        "gcp-api-key",
        re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
        "Possible Google Cloud API key detected",
    ),
    (
        "slack-token",
        re.compile(r"xox[bpars]-[0-9A-Za-z\-]{10,}"),
        "Possible Slack token detected",
    ),
]
"""Compiled (rule-id, pattern, message) tuples for secret detection."""


class SecretAnalyzer(BaseAnalyzer):
    """Detects exposed secrets, credentials, and tokens in source files.

    Applies a bank of regular-expression patterns against each line of
    every scanned file and emits ``critical`` or ``high`` severity
    findings for matches.
    """

    @property
    def name(self) -> str:
        """Returns ``"secret-scanner"``."""
        return "secret-scanner"

    @property
    def category(self) -> str:
        """Returns ``"security"``."""
        return "security"

    async def analyze(self, files: list[ScannedFile]) -> list[Finding]:
        """Scan all files for secret patterns.

        Args:
            files: Pre-scanned source files.

        Returns:
            Findings for every line matching a secret pattern.
        """
        findings: list[Finding] = []

        for scanned in files:
            lines = scanned.content.splitlines()
            for line_num, line in enumerate(lines, start=1):
                for rule_id, pattern, message in _SECRET_PATTERNS:
                    if pattern.search(line):
                        severity = self._severity_for_rule(rule_id)
                        findings.append(
                            Finding(
                                severity=severity,
                                category="security",
                                rule=rule_id,
                                message=message,
                                file_path=scanned.path,
                                line_number=line_num,
                                snippet=line.strip()[:120],
                            )
                        )

        return findings

    @staticmethod
    def _severity_for_rule(rule_id: str) -> str:
        """Map a rule identifier to its severity level.

        Args:
            rule_id: The machine-readable rule name.

        Returns:
            ``"critical"`` for private keys and known provider keys,
            ``"high"`` for everything else.
        """
        critical_rules = {"aws-access-key", "aws-secret-key", "private-key"}
        return "critical" if rule_id in critical_rules else "high"
