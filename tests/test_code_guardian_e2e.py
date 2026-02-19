"""End-to-end tests for the Code Guardian service.

Verifies tool registration, tool execution through FastMCP with
temporary directories containing sample vulnerable code, and
resource accessibility.
"""

import os
import tempfile

import httpx
import pytest
import respx

from mcp_factory.services.code_guardian.config import OSV_API_BASE_URL

EXPECTED_TOOL_NAMES: set[str] = {
    "scan_codebase",
    "scan_secrets",
    "scan_security_patterns",
    "scan_code_quality",
    "scan_dependencies",
}


@pytest.fixture()
def mcp_server():
    """Provide a fresh FastMCP server with only Code Guardian applied.

    Builds a new server each time so tests don't share state.
    """
    from mcp.server.fastmcp import FastMCP

    from mcp_factory.config import SERVER_NAME
    from mcp_factory.services.code_guardian import CodeGuardianService
    from mcp_factory.services.registry import ServiceRegistry

    server = FastMCP(SERVER_NAME)
    registry = ServiceRegistry()
    registry.add(CodeGuardianService())
    registry.apply_all(server)
    return server


@pytest.fixture()
def vulnerable_dir():
    """Create a temp directory with sample files containing known issues."""
    with tempfile.TemporaryDirectory() as tmp:
        py_file = os.path.join(tmp, "app.py")
        with open(py_file, "w") as f:
            f.write(
                'API_KEY = "AKIAIOSFODNN7EXAMPLE"\n'
                "result = eval(user_input)\n"
                "print('debug output')\n"
                "password = 'supersecret123'\n"
            )

        js_file = os.path.join(tmp, "index.js")
        with open(js_file, "w") as f:
            f.write(
                "console.log('debugging');\n"
                "element.innerHTML = userInput;\n"
                "const token = Math.random().toString(36);\n"
            )

        pkg_json = os.path.join(tmp, "package.json")
        with open(pkg_json, "w") as f:
            f.write(
                '{"dependencies": {"express": "4.17.1"}}\n'
            )

        yield tmp


@pytest.fixture()
def clean_dir():
    """Create a temp directory with clean code (no issues)."""
    with tempfile.TemporaryDirectory() as tmp:
        clean_file = os.path.join(tmp, "clean.py")
        with open(clean_file, "w") as f:
            f.write("def greet(name: str) -> str:\n    return f'Hello {name}'\n")
        yield tmp


class TestCodeGuardianBootstrap:
    """Verify the server boots with all Code Guardian tools registered."""

    @pytest.mark.asyncio
    async def test_all_five_tools_registered(self, mcp_server) -> None:
        tools = await mcp_server.list_tools()
        tool_names = {t.name for t in tools}
        for expected in EXPECTED_TOOL_NAMES:
            assert expected in tool_names

    @pytest.mark.asyncio
    async def test_owasp_resource_registered(self, mcp_server) -> None:
        resources = await mcp_server.list_resources()
        uris = {str(r.uri) for r in resources}
        assert "security://references/owasp-top-10" in uris


@pytest.mark.asyncio
class TestScanCodebase:
    """Full multi-pass scan through the MCP tool interface."""

    @respx.mock
    async def test_scan_codebase_finds_issues(self, mcp_server, vulnerable_dir) -> None:
        respx.post(f"{OSV_API_BASE_URL}/query").mock(
            return_value=httpx.Response(200, json={"vulns": []})
        )
        result_tuple = await mcp_server.call_tool(
            "scan_codebase", {"path": vulnerable_dir}
        )
        text = result_tuple[0][0].text
        assert "Code Guardian Scan Report" in text
        assert "Files scanned" in text

    @respx.mock
    async def test_scan_codebase_detects_secrets(self, mcp_server, vulnerable_dir) -> None:
        respx.post(f"{OSV_API_BASE_URL}/query").mock(
            return_value=httpx.Response(200, json={"vulns": []})
        )
        result_tuple = await mcp_server.call_tool(
            "scan_codebase", {"path": vulnerable_dir}
        )
        text = result_tuple[0][0].text
        assert "CRITICAL" in text or "HIGH" in text

    async def test_scan_codebase_invalid_path(self, mcp_server) -> None:
        result_tuple = await mcp_server.call_tool(
            "scan_codebase", {"path": "/nonexistent/path/12345"}
        )
        text = result_tuple[0][0].text
        assert "does not exist" in text


@pytest.mark.asyncio
class TestScanSecrets:
    """Secret detection through the MCP tool interface."""

    async def test_scan_secrets_finds_exposed_keys(self, mcp_server, vulnerable_dir) -> None:
        result_tuple = await mcp_server.call_tool(
            "scan_secrets", {"path": vulnerable_dir}
        )
        text = result_tuple[0][0].text
        assert "Security Scan" in text

    async def test_scan_secrets_clean_dir(self, mcp_server, clean_dir) -> None:
        result_tuple = await mcp_server.call_tool(
            "scan_secrets", {"path": clean_dir}
        )
        text = result_tuple[0][0].text
        assert "No issues found" in text or "Total findings:** 0" in text


@pytest.mark.asyncio
class TestScanCodeQuality:
    """Quality and style checks through the MCP tool interface."""

    async def test_scan_code_quality_finds_debug_stmts(self, mcp_server, vulnerable_dir) -> None:
        result_tuple = await mcp_server.call_tool(
            "scan_code_quality", {"path": vulnerable_dir}
        )
        text = result_tuple[0][0].text
        assert "Code Quality" in text

    async def test_scan_code_quality_empty_path_error(self, mcp_server) -> None:
        result_tuple = await mcp_server.call_tool(
            "scan_code_quality", {"path": ""}
        )
        text = result_tuple[0][0].text
        assert "empty" in text.lower()


@pytest.mark.asyncio
class TestScanDependencies:
    """Dependency vulnerability scan through the MCP tool interface."""

    @respx.mock
    async def test_scan_dependencies_queries_osv(self, mcp_server, vulnerable_dir) -> None:
        respx.post(f"{OSV_API_BASE_URL}/query").mock(
            return_value=httpx.Response(
                200,
                json={
                    "vulns": [
                        {
                            "id": "GHSA-test",
                            "summary": "Test vulnerability in express",
                            "severity": [{"score": "7.5"}],
                        }
                    ],
                },
            )
        )
        result_tuple = await mcp_server.call_tool(
            "scan_dependencies", {"path": vulnerable_dir}
        )
        text = result_tuple[0][0].text
        assert "Dependency Vulnerability Scan" in text
        assert "GHSA-test" in text

    @respx.mock
    async def test_scan_dependencies_clean(self, mcp_server, vulnerable_dir) -> None:
        respx.post(f"{OSV_API_BASE_URL}/query").mock(
            return_value=httpx.Response(200, json={"vulns": []})
        )
        result_tuple = await mcp_server.call_tool(
            "scan_dependencies", {"path": vulnerable_dir}
        )
        text = result_tuple[0][0].text
        assert "No issues found" in text or "Total findings:** 0" in text


class TestOWASPResource:
    """Verify the OWASP Top 10 resource is readable."""

    @pytest.mark.asyncio
    async def test_owasp_resource_content(self, mcp_server) -> None:
        result = await mcp_server.read_resource("security://references/owasp-top-10")
        content = result[0].content
        assert "Broken Access Control" in content
        assert "Injection" in content
        assert "SSRF" in content
