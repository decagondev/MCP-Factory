"""Tests for mcp_factory.services.code_guardian.analyzers.debug_statements."""

import pytest

from mcp_factory.services.code_guardian.analyzers.debug_statements import DebugStatementAnalyzer
from mcp_factory.services.code_guardian.models import ScannedFile


def _make_file(content: str, language: str = "python", path: str = "test.py") -> list[ScannedFile]:
    """Wrap content in a single-file list for the analyzer."""
    return [ScannedFile(path=path, content=content, language=language, line_count=content.count("\n") + 1)]


@pytest.mark.asyncio
class TestDebugStatementAnalyzer:
    """Verify debug/print statement detection across languages."""

    async def test_name_and_category(self) -> None:
        analyzer = DebugStatementAnalyzer()
        assert analyzer.name == "debug-statement-analyzer"
        assert analyzer.category == "quality"

    async def test_detects_console_log_js(self) -> None:
        code = 'console.log("debug");\n'
        findings = await DebugStatementAnalyzer().analyze(
            _make_file(code, language="javascript", path="app.js")
        )
        assert len(findings) >= 1
        assert findings[0].rule == "debug-statement"

    async def test_detects_console_warn_ts(self) -> None:
        code = "console.warn('warning');\n"
        findings = await DebugStatementAnalyzer().analyze(
            _make_file(code, language="typescript", path="app.ts")
        )
        assert len(findings) >= 1

    async def test_detects_console_error_js(self) -> None:
        code = "console.error('err');\n"
        findings = await DebugStatementAnalyzer().analyze(
            _make_file(code, language="javascript", path="app.js")
        )
        assert len(findings) >= 1

    async def test_detects_python_print(self) -> None:
        code = "print('hello')\n"
        findings = await DebugStatementAnalyzer().analyze(_make_file(code))
        assert len(findings) >= 1

    async def test_detects_java_system_out(self) -> None:
        code = 'System.out.println("debug");\n'
        findings = await DebugStatementAnalyzer().analyze(
            _make_file(code, language="java", path="Main.java")
        )
        assert len(findings) >= 1

    async def test_detects_go_fmt_println(self) -> None:
        code = 'fmt.Println("debug")\n'
        findings = await DebugStatementAnalyzer().analyze(
            _make_file(code, language="go", path="main.go")
        )
        assert len(findings) >= 1

    async def test_detects_cpp_cout(self) -> None:
        code = 'std::cout << "debug" << std::endl;\n'
        findings = await DebugStatementAnalyzer().analyze(
            _make_file(code, language="cpp", path="main.cpp")
        )
        assert len(findings) >= 1

    async def test_detects_c_printf(self) -> None:
        code = 'printf("debug %d\\n", x);\n'
        findings = await DebugStatementAnalyzer().analyze(
            _make_file(code, language="c", path="main.c")
        )
        assert len(findings) >= 1

    async def test_detects_rust_dbg(self) -> None:
        code = "dbg!(value);\n"
        findings = await DebugStatementAnalyzer().analyze(
            _make_file(code, language="rust", path="main.rs")
        )
        assert len(findings) >= 1

    async def test_detects_php_var_dump(self) -> None:
        code = "var_dump($data);\n"
        findings = await DebugStatementAnalyzer().analyze(
            _make_file(code, language="php", path="index.php")
        )
        assert len(findings) >= 1

    async def test_ignores_comments(self) -> None:
        code = "# print('this is a comment')\n"
        findings = await DebugStatementAnalyzer().analyze(_make_file(code))
        assert len(findings) == 0

    async def test_language_scoping(self) -> None:
        code = 'console.log("test");\n'
        findings = await DebugStatementAnalyzer().analyze(
            _make_file(code, language="python", path="test.py")
        )
        console_findings = [f for f in findings if "console" in f.message]
        assert len(console_findings) == 0

    async def test_clean_code_no_findings(self) -> None:
        code = "def greet(name: str) -> str:\n    return f'Hello {name}'\n"
        findings = await DebugStatementAnalyzer().analyze(_make_file(code))
        assert len(findings) == 0

    async def test_finding_severity_is_low(self) -> None:
        code = "print('debug')\n"
        findings = await DebugStatementAnalyzer().analyze(_make_file(code))
        assert all(f.severity == "low" for f in findings)

    async def test_finding_includes_line_number(self) -> None:
        code = "x = 1\nprint('debug')\ny = 2\n"
        findings = await DebugStatementAnalyzer().analyze(_make_file(code))
        assert any(f.line_number == 2 for f in findings)
