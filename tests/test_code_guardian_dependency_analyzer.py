"""Tests for nasa_apod.services.code_guardian.analyzers.dependencies."""

import httpx
import pytest
import respx

from nasa_apod.services.code_guardian.analyzers.dependencies import DependencyAnalyzer
from nasa_apod.services.code_guardian.config import OSV_API_BASE_URL
from nasa_apod.services.code_guardian.models import ScannedFile
from nasa_apod.services.code_guardian.osv_client import OsvClient

SAMPLE_PACKAGE_JSON = """{
  "name": "my-app",
  "dependencies": {
    "express": "^4.18.2",
    "lodash": "~4.17.21"
  },
  "devDependencies": {
    "jest": "^29.0.0"
  }
}"""

SAMPLE_REQUIREMENTS_TXT = """flask>=2.3.0
requests==2.31.0
numpy
# comment
-r other.txt
"""

SAMPLE_GO_MOD = """module example.com/myapp

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    golang.org/x/text v0.13.0
)
"""

SAMPLE_CARGO_TOML = """[package]
name = "my-app"

[dependencies]
serde = "1.0"
tokio = "1.32"
"""

SAMPLE_GEMFILE_LOCK = """GEM
  remote: https://rubygems.org/
  specs:
    rails (7.0.8)
    nokogiri (1.15.4)

PLATFORMS
  ruby
"""


def _make_client() -> OsvClient:
    """Create an OsvClient for testing."""
    return OsvClient(base_url=OSV_API_BASE_URL, api_key="", timeout=10.0)


def _make_file(content: str, path: str, language: str = "json") -> list[ScannedFile]:
    """Wrap manifest content in a single-file list."""
    return [ScannedFile(path=path, content=content, language=language, line_count=content.count("\n") + 1)]


VULN_RESPONSE = {
    "vulns": [
        {
            "id": "GHSA-test-vuln",
            "summary": "Test vulnerability",
            "severity": [{"type": "CVSS_V3", "score": "7.5"}],
        }
    ]
}

EMPTY_RESPONSE = {"vulns": []}


class TestDependencyParsing:
    """Verify manifest parsing without network calls."""

    def test_parse_package_json(self) -> None:
        deps = DependencyAnalyzer._parse_package_json(SAMPLE_PACKAGE_JSON)
        names = {d[0] for d in deps}
        assert "express" in names
        assert "lodash" in names
        assert "jest" in names
        express_ver = next(v for n, v in deps if n == "express")
        assert express_ver == "4.18.2"

    def test_parse_requirements_txt(self) -> None:
        deps = DependencyAnalyzer._parse_requirements_txt(SAMPLE_REQUIREMENTS_TXT)
        names = {d[0] for d in deps}
        assert "flask" in names
        assert "requests" in names
        assert "numpy" in names
        requests_ver = next(v for n, v in deps if n == "requests")
        assert requests_ver == "2.31.0"

    def test_parse_go_mod(self) -> None:
        deps = DependencyAnalyzer._parse_go_mod(SAMPLE_GO_MOD)
        names = {d[0] for d in deps}
        assert "github.com/gin-gonic/gin" in names
        assert "golang.org/x/text" in names
        gin_ver = next(v for n, v in deps if n == "github.com/gin-gonic/gin")
        assert gin_ver == "1.9.1"

    def test_parse_cargo_toml(self) -> None:
        deps = DependencyAnalyzer._parse_cargo_toml(SAMPLE_CARGO_TOML)
        names = {d[0] for d in deps}
        assert "serde" in names
        assert "tokio" in names
        serde_ver = next(v for n, v in deps if n == "serde")
        assert serde_ver == "1.0"

    def test_parse_gemfile_lock(self) -> None:
        deps = DependencyAnalyzer._parse_gemfile_lock(SAMPLE_GEMFILE_LOCK)
        names = {d[0] for d in deps}
        assert "rails" in names
        assert "nokogiri" in names

    def test_parse_invalid_json_returns_empty(self) -> None:
        deps = DependencyAnalyzer._parse_package_json("not valid json")
        assert deps == []


@pytest.mark.asyncio
class TestDependencyAnalyzer:
    """Verify end-to-end dependency analysis with mocked OSV."""

    async def test_name_and_category(self) -> None:
        analyzer = DependencyAnalyzer(_make_client())
        assert analyzer.name == "dependency-analyzer"
        assert analyzer.category == "vulnerability"

    @respx.mock
    async def test_finds_vulnerabilities_in_package_json(self) -> None:
        respx.post(f"{OSV_API_BASE_URL}/query").mock(
            return_value=httpx.Response(200, json=VULN_RESPONSE)
        )
        analyzer = DependencyAnalyzer(_make_client())
        files = _make_file(SAMPLE_PACKAGE_JSON, "package.json")
        findings = await analyzer.analyze(files)
        assert len(findings) >= 1
        assert all(f.rule == "known-vulnerability" for f in findings)
        assert any("GHSA-test-vuln" in f.message for f in findings)

    @respx.mock
    async def test_no_findings_for_clean_deps(self) -> None:
        respx.post(f"{OSV_API_BASE_URL}/query").mock(
            return_value=httpx.Response(200, json=EMPTY_RESPONSE)
        )
        analyzer = DependencyAnalyzer(_make_client())
        files = _make_file(SAMPLE_REQUIREMENTS_TXT, "requirements.txt", language="text")
        findings = await analyzer.analyze(files)
        assert len(findings) == 0

    @respx.mock
    async def test_skips_non_manifest_files(self) -> None:
        analyzer = DependencyAnalyzer(_make_client())
        files = [ScannedFile(path="app.py", content="x=1\n", language="python", line_count=1)]
        findings = await analyzer.analyze(files)
        assert len(findings) == 0

    @respx.mock
    async def test_handles_api_failure_gracefully(self) -> None:
        respx.post(f"{OSV_API_BASE_URL}/query").mock(
            return_value=httpx.Response(500, text="Server Error")
        )
        analyzer = DependencyAnalyzer(_make_client())
        files = _make_file(SAMPLE_PACKAGE_JSON, "package.json")
        findings = await analyzer.analyze(files)
        assert len(findings) == 0


class TestSeverityMapping:
    """Verify CVSS-to-severity mapping (synchronous, no async mark)."""

    def test_severity_mapping_critical(self) -> None:
        vuln = {"severity": [{"score": "9.5"}]}
        assert DependencyAnalyzer._determine_severity(vuln) == "critical"

    def test_severity_mapping_high(self) -> None:
        vuln = {"severity": [{"score": "7.5"}]}
        assert DependencyAnalyzer._determine_severity(vuln) == "high"

    def test_severity_mapping_medium(self) -> None:
        vuln = {"severity": [{"score": "5.0"}]}
        assert DependencyAnalyzer._determine_severity(vuln) == "medium"

    def test_severity_mapping_low(self) -> None:
        vuln = {"severity": [{"score": "2.0"}]}
        assert DependencyAnalyzer._determine_severity(vuln) == "low"

    def test_severity_fallback_to_database_specific(self) -> None:
        vuln = {"database_specific": {"severity": "CRITICAL"}}
        assert DependencyAnalyzer._determine_severity(vuln) == "critical"

    def test_severity_fallback_default_high(self) -> None:
        vuln = {}
        assert DependencyAnalyzer._determine_severity(vuln) == "high"
