"""Code Guardian service plugin.

Exposes :class:`CodeGuardianService`, which satisfies the
:class:`~mcp_factory.services.base.ServicePlugin` protocol and
registers code-analysis tools and resources onto a FastMCP server.

The service performs multi-pass analysis of codebases including
secret detection, OWASP security pattern matching, code quality
checks, style linting, and dependency vulnerability scanning via
the OSV.dev API.
"""

import os

from mcp.server.fastmcp import FastMCP

from mcp_factory.services.code_guardian.analyzers import AnalyzerRegistry
from mcp_factory.services.code_guardian.analyzers.code_quality import CodeQualityAnalyzer
from mcp_factory.services.code_guardian.analyzers.debug_statements import DebugStatementAnalyzer
from mcp_factory.services.code_guardian.analyzers.dependencies import DependencyAnalyzer
from mcp_factory.services.code_guardian.analyzers.secrets import SecretAnalyzer
from mcp_factory.services.code_guardian.analyzers.security_patterns import SecurityPatternAnalyzer
from mcp_factory.services.code_guardian.analyzers.style import StyleAnalyzer
from mcp_factory.services.code_guardian.config import (
    OSV_API_BASE_URL,
    OSV_API_KEY,
    OSV_REQUEST_TIMEOUT_SECONDS,
)
from mcp_factory.services.code_guardian.formatter import CodeGuardianFormatter
from mcp_factory.services.code_guardian.osv_client import OsvClient
from mcp_factory.services.code_guardian.scanner import FileScanner
from mcp_factory.services.code_guardian.validation import validate_scan_path

__all__ = ["CodeGuardianService"]


class CodeGuardianService:
    """Code Guardian ServicePlugin -- registers analysis tools and resources.

    Composes a :class:`FileScanner`, an :class:`AnalyzerRegistry`
    populated with all six analyzers, an :class:`OsvClient`, and a
    :class:`CodeGuardianFormatter`.  Registers five MCP tools and one
    reference resource onto the server.
    """

    def __init__(self) -> None:
        self._osv_client = OsvClient(
            base_url=OSV_API_BASE_URL,
            api_key=OSV_API_KEY,
            timeout=OSV_REQUEST_TIMEOUT_SECONDS,
        )
        self._formatter = CodeGuardianFormatter()

        self._registry = AnalyzerRegistry()
        self._registry.add(SecretAnalyzer())
        self._registry.add(SecurityPatternAnalyzer())
        self._registry.add(DebugStatementAnalyzer())
        self._registry.add(CodeQualityAnalyzer())
        self._registry.add(StyleAnalyzer())
        self._registry.add(DependencyAnalyzer(self._osv_client))

    def register(self, mcp: FastMCP) -> None:
        """Register Code Guardian tools and the OWASP reference resource.

        Args:
            mcp: The FastMCP server instance to register onto.
        """
        registry = self._registry
        formatter = self._formatter

        @mcp.tool()
        async def scan_codebase(path: str) -> str:
            """Run a full multi-pass security and quality scan on a codebase directory.

            Executes all analyzers: secret detection, OWASP security patterns,
            debug statement detection, code quality checks, style linting, and
            dependency vulnerability scanning via OSV.dev.

            Use this when asked to review, audit, or scan a codebase for issues.
            """
            error = validate_scan_path(path)
            if error:
                return f"\u274c {error}"

            expanded = os.path.expanduser(path.strip())
            scanner = FileScanner(expanded)
            files = await scanner.scan()
            if not files:
                return "\u274c No supported source files found in the specified directory."

            result = await registry.run_all(files)
            return formatter.format_scan_result(
                result, header="## Full Codebase Scan"
            )

        @mcp.tool()
        async def scan_secrets(path: str) -> str:
            """Scan a codebase directory for exposed secrets, API keys, and credentials.

            Detects AWS keys, GitHub tokens, GCP keys, Slack tokens, JWTs,
            private keys, database connection strings, and generic hardcoded
            secrets.

            Use this when asked to check for leaked credentials or secrets.
            """
            error = validate_scan_path(path)
            if error:
                return f"\u274c {error}"

            expanded = os.path.expanduser(path.strip())
            scanner = FileScanner(expanded)
            files = await scanner.scan()
            if not files:
                return "\u274c No supported source files found in the specified directory."

            result = await registry.run_by_category("security", files)
            return formatter.format_scan_result(
                result, header="## Security Scan (Secrets & Patterns)"
            )

        @mcp.tool()
        async def scan_security_patterns(path: str) -> str:
            """Scan a codebase for OWASP-style security antipatterns.

            Detects SQL injection vectors, XSS sinks, eval/exec usage,
            insecure cryptographic primitives, path traversal, insecure
            deserialization, and shell injection patterns.

            Use this when asked about security vulnerabilities or OWASP compliance.
            """
            error = validate_scan_path(path)
            if error:
                return f"\u274c {error}"

            expanded = os.path.expanduser(path.strip())
            scanner = FileScanner(expanded)
            files = await scanner.scan()
            if not files:
                return "\u274c No supported source files found in the specified directory."

            result = await registry.run_by_category("security", files)
            return formatter.format_scan_result(
                result, header="## Security Pattern Scan"
            )

        @mcp.tool()
        async def scan_code_quality(path: str) -> str:
            """Scan a codebase for code quality and style issues.

            Checks for debug/print statements, oversized files, long lines,
            deep nesting, too many function parameters, trailing whitespace,
            TODO/FIXME comments, mixed indentation, superfluous comments,
            and naming convention violations (PEP 8 for Python, camelCase
            for JS/TS).

            Use this when asked to check code quality, readability, or style.
            """
            error = validate_scan_path(path)
            if error:
                return f"\u274c {error}"

            expanded = os.path.expanduser(path.strip())
            scanner = FileScanner(expanded)
            files = await scanner.scan()
            if not files:
                return "\u274c No supported source files found in the specified directory."

            quality_result = await registry.run_by_category("quality", files)
            style_result = await registry.run_by_category("style", files)

            quality_result.findings.extend(style_result.findings)
            quality_result.analyzers_run.extend(style_result.analyzers_run)

            return formatter.format_scan_result(
                quality_result, header="## Code Quality & Style Scan"
            )

        @mcp.tool()
        async def scan_dependencies(path: str) -> str:
            """Scan a project's dependency manifests for known CVEs via OSV.dev.

            Parses package.json, requirements.txt, pyproject.toml, go.mod,
            Cargo.toml, and Gemfile.lock, then queries the OSV vulnerability
            database for each dependency.

            Use this when asked to check dependencies for vulnerabilities or CVEs.
            """
            error = validate_scan_path(path)
            if error:
                return f"\u274c {error}"

            expanded = os.path.expanduser(path.strip())
            scanner = FileScanner(expanded)
            files = await scanner.scan()
            if not files:
                return "\u274c No supported source files found in the specified directory."

            result = await registry.run_by_category("vulnerability", files)
            return formatter.format_scan_result(
                result, header="## Dependency Vulnerability Scan"
            )

        @mcp.resource("security://references/owasp-top-10")
        def owasp_top_10_reference() -> str:
            """OWASP Top 10 (2021) quick reference for code security reviews."""
            return (
                "\n## OWASP Top 10 (2021) Quick Reference\n\n"
                "**A01:2021 -- Broken Access Control**\n"
                "Restrictions on authenticated users are not properly enforced.\n\n"
                "**A02:2021 -- Cryptographic Failures**\n"
                "Failures related to cryptography that lead to data exposure.\n\n"
                "**A03:2021 -- Injection**\n"
                "SQL, NoSQL, OS, LDAP injection via untrusted data.\n\n"
                "**A04:2021 -- Insecure Design**\n"
                "Missing or ineffective security controls in design.\n\n"
                "**A05:2021 -- Security Misconfiguration**\n"
                "Insecure default configs, open cloud storage, verbose errors.\n\n"
                "**A06:2021 -- Vulnerable and Outdated Components**\n"
                "Using components with known vulnerabilities.\n\n"
                "**A07:2021 -- Identification and Authentication Failures**\n"
                "Weak authentication, session management flaws.\n\n"
                "**A08:2021 -- Software and Data Integrity Failures**\n"
                "Code and infrastructure without integrity verification.\n\n"
                "**A09:2021 -- Security Logging and Monitoring Failures**\n"
                "Insufficient logging, detection, and response.\n\n"
                "**A10:2021 -- Server-Side Request Forgery (SSRF)**\n"
                "Web application fetches remote resources without validation.\n"
            )
