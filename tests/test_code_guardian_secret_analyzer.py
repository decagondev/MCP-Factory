"""Tests for mcp_factory.services.code_guardian.analyzers.secrets."""

import pytest

from mcp_factory.services.code_guardian.analyzers.secrets import SecretAnalyzer
from mcp_factory.services.code_guardian.models import ScannedFile


def _make_file(content: str, language: str = "python", path: str = "test.py") -> list[ScannedFile]:
    """Wrap content in a single-file list for the analyzer."""
    return [ScannedFile(path=path, content=content, language=language, line_count=content.count("\n") + 1)]


@pytest.mark.asyncio
class TestSecretAnalyzer:
    """Verify secret detection patterns."""

    async def test_name_and_category(self) -> None:
        analyzer = SecretAnalyzer()
        assert analyzer.name == "secret-scanner"
        assert analyzer.category == "security"

    async def test_detects_aws_access_key(self) -> None:
        code = 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n'
        findings = await SecretAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "aws-access-key" in rules

    async def test_detects_aws_secret_key(self) -> None:
        code = 'aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"\n'
        findings = await SecretAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "aws-secret-key" in rules

    async def test_detects_github_token(self) -> None:
        code = 'GITHUB_TOKEN = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk"\n'
        findings = await SecretAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "github-token" in rules

    async def test_detects_generic_api_key(self) -> None:
        code = 'api_key = "sk_live_1234567890abcdefghij"\n'
        findings = await SecretAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "generic-api-key" in rules

    async def test_detects_generic_secret(self) -> None:
        code = "password = 'SuperSecretPassword123!'\n"
        findings = await SecretAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "generic-secret" in rules

    async def test_detects_private_key(self) -> None:
        code = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpA...\n"
        findings = await SecretAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "private-key" in rules
        assert any(f.severity == "critical" for f in findings)

    async def test_detects_jwt_token(self) -> None:
        code = 'token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123def456"\n'
        findings = await SecretAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "jwt-token" in rules

    async def test_detects_connection_string(self) -> None:
        code = 'DB_URL = "postgresql://user:pass@host:5432/mydb"\n'
        findings = await SecretAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "connection-string" in rules

    async def test_detects_gcp_key(self) -> None:
        code = 'GCP_KEY = "AIzaSyA-valid-looking-gcp-api-key-here1"\n'
        findings = await SecretAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "gcp-api-key" in rules

    async def test_detects_slack_token(self) -> None:
        code = 'SLACK = "xoxb-1234567890-abcdefghij"\n'
        findings = await SecretAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "slack-token" in rules

    async def test_clean_code_produces_no_findings(self) -> None:
        code = "def greet(name: str) -> str:\n    return f'Hello {name}'\n"
        findings = await SecretAnalyzer().analyze(_make_file(code))
        assert len(findings) == 0

    async def test_finding_includes_line_number(self) -> None:
        code = "line1\nline2\napi_key = 'sk_live_1234567890abcdefghij'\nline4\n"
        findings = await SecretAnalyzer().analyze(_make_file(code))
        assert any(f.line_number == 3 for f in findings)

    async def test_finding_includes_snippet(self) -> None:
        code = "password = 'mysupersecretvalue'\n"
        findings = await SecretAnalyzer().analyze(_make_file(code))
        assert all(f.snippet is not None for f in findings)

    async def test_aws_key_is_critical_severity(self) -> None:
        code = 'key = "AKIAIOSFODNN7EXAMPLE"\n'
        findings = await SecretAnalyzer().analyze(_make_file(code))
        aws_findings = [f for f in findings if f.rule == "aws-access-key"]
        assert all(f.severity == "critical" for f in aws_findings)

    async def test_generic_token_is_high_severity(self) -> None:
        code = 'SLACK = "xoxb-1234567890-abcdefghij"\n'
        findings = await SecretAnalyzer().analyze(_make_file(code))
        slack_findings = [f for f in findings if f.rule == "slack-token"]
        assert all(f.severity == "high" for f in slack_findings)
