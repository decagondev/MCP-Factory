"""Tests for nasa_apod.services.code_guardian.analyzers.security_patterns."""

import pytest

from nasa_apod.services.code_guardian.analyzers.security_patterns import SecurityPatternAnalyzer
from nasa_apod.services.code_guardian.models import ScannedFile


def _make_file(
    content: str, language: str = "python", path: str = "test.py"
) -> list[ScannedFile]:
    """Wrap content in a single-file list for the analyzer."""
    return [ScannedFile(path=path, content=content, language=language, line_count=content.count("\n") + 1)]


@pytest.mark.asyncio
class TestSecurityPatternAnalyzer:
    """Verify OWASP-style security pattern detection."""

    async def test_name_and_category(self) -> None:
        analyzer = SecurityPatternAnalyzer()
        assert analyzer.name == "security-pattern-analyzer"
        assert analyzer.category == "security"

    async def test_detects_sql_injection_format(self) -> None:
        code = 'cursor.execute("SELECT * FROM users WHERE id=" + user_id)\n'
        findings = await SecurityPatternAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "sql-injection" in rules

    async def test_detects_sql_injection_fstring(self) -> None:
        code = "query = f\"SELECT * FROM users WHERE id={user_id}\"\n"
        findings = await SecurityPatternAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "sql-injection-fstring" in rules

    async def test_detects_innerhtml_xss(self) -> None:
        code = "element.innerHTML = userInput;\n"
        findings = await SecurityPatternAnalyzer().analyze(
            _make_file(code, language="javascript", path="app.js")
        )
        rules = {f.rule for f in findings}
        assert "xss-innerhtml" in rules

    async def test_detects_dangerously_set_inner_html(self) -> None:
        code = '<div dangerouslySetInnerHTML={{__html: content}} />\n'
        findings = await SecurityPatternAnalyzer().analyze(
            _make_file(code, language="javascript", path="component.jsx")
        )
        rules = {f.rule for f in findings}
        assert "xss-dangerously-set" in rules

    async def test_detects_document_write(self) -> None:
        code = "document.write(data);\n"
        findings = await SecurityPatternAnalyzer().analyze(
            _make_file(code, language="javascript", path="page.js")
        )
        rules = {f.rule for f in findings}
        assert "xss-document-write" in rules

    async def test_detects_eval_usage(self) -> None:
        code = "result = eval(user_input)\n"
        findings = await SecurityPatternAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "eval-usage" in rules

    async def test_detects_md5_usage(self) -> None:
        code = "import hashlib\nhash_val = hashlib.md5(data)\n"
        findings = await SecurityPatternAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "insecure-hash-md5" in rules

    async def test_detects_sha1_usage(self) -> None:
        code = "hash_val = sha1(password)\n"
        findings = await SecurityPatternAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "insecure-hash-sha1" in rules

    async def test_detects_path_traversal(self) -> None:
        code = "data = open('../../../etc/passwd')\n"
        findings = await SecurityPatternAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "path-traversal" in rules

    async def test_detects_pickle_deserialization(self) -> None:
        code = "obj = pickle.load(untrusted_data)\n"
        findings = await SecurityPatternAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "insecure-deserialization" in rules

    async def test_detects_insecure_random_js(self) -> None:
        code = "const token = Math.random().toString(36);\n"
        findings = await SecurityPatternAnalyzer().analyze(
            _make_file(code, language="javascript", path="auth.js")
        )
        rules = {f.rule for f in findings}
        assert "insecure-random" in rules

    async def test_detects_hardcoded_ip(self) -> None:
        code = 'HOST = "192.168.1.100"\n'
        findings = await SecurityPatternAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "hardcoded-ip" in rules

    async def test_detects_subprocess_shell_true(self) -> None:
        code = 'subprocess.call(cmd, shell=True)\n'
        findings = await SecurityPatternAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "subprocess-shell-true" in rules

    async def test_detects_exec_usage(self) -> None:
        code = 'exec(user_code)\n'
        findings = await SecurityPatternAnalyzer().analyze(_make_file(code))
        rules = {f.rule for f in findings}
        assert "exec-usage" in rules

    async def test_language_scoping_ignores_irrelevant(self) -> None:
        code = "result = eval(data)\n"
        findings = await SecurityPatternAnalyzer().analyze(
            _make_file(code, language="sql", path="query.sql")
        )
        eval_findings = [f for f in findings if f.rule == "eval-usage"]
        assert len(eval_findings) == 0

    async def test_clean_code_produces_no_findings(self) -> None:
        code = (
            "def get_user(user_id: int) -> dict:\n"
            "    return db.query(User).filter_by(id=user_id).first()\n"
        )
        findings = await SecurityPatternAnalyzer().analyze(_make_file(code))
        assert len(findings) == 0

    async def test_finding_includes_line_number_and_snippet(self) -> None:
        code = "line1\nresult = eval(user_input)\nline3\n"
        findings = await SecurityPatternAnalyzer().analyze(_make_file(code))
        eval_findings = [f for f in findings if f.rule == "eval-usage"]
        assert eval_findings[0].line_number == 2
        assert eval_findings[0].snippet is not None
