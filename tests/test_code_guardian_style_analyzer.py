"""Tests for nasa_apod.services.code_guardian.analyzers.style."""

import pytest

from nasa_apod.services.code_guardian.analyzers.style import StyleAnalyzer
from nasa_apod.services.code_guardian.models import ScannedFile


def _make_file(content: str, language: str = "python", path: str = "test.py") -> list[ScannedFile]:
    """Wrap content in a single-file list for the analyzer."""
    return [ScannedFile(path=path, content=content, language=language, line_count=content.count("\n") + 1)]


@pytest.mark.asyncio
class TestStyleAnalyzer:
    """Verify style checks: whitespace, comments, naming."""

    async def test_name_and_category(self) -> None:
        analyzer = StyleAnalyzer()
        assert analyzer.name == "style-analyzer"
        assert analyzer.category == "style"

    async def test_detects_trailing_whitespace(self) -> None:
        content = "x = 1   \ny = 2\n"
        findings = await StyleAnalyzer().analyze(_make_file(content))
        ws_findings = [f for f in findings if f.rule == "trailing-whitespace"]
        assert len(ws_findings) >= 1
        assert ws_findings[0].line_number == 1

    async def test_no_trailing_ws_on_clean_file(self) -> None:
        content = "x = 1\ny = 2\n"
        findings = await StyleAnalyzer().analyze(_make_file(content))
        ws_findings = [f for f in findings if f.rule == "trailing-whitespace"]
        assert len(ws_findings) == 0

    async def test_detects_todo_comment(self) -> None:
        content = "x = 1  # TODO: fix this\n"
        findings = await StyleAnalyzer().analyze(_make_file(content))
        todo_findings = [f for f in findings if f.rule == "todo-comment"]
        assert len(todo_findings) >= 1

    async def test_detects_fixme_comment(self) -> None:
        content = "x = 1  # FIXME: broken\n"
        findings = await StyleAnalyzer().analyze(_make_file(content))
        todo_findings = [f for f in findings if f.rule == "todo-comment"]
        assert len(todo_findings) >= 1

    async def test_detects_hack_comment(self) -> None:
        content = "x = 1  # HACK workaround\n"
        findings = await StyleAnalyzer().analyze(_make_file(content))
        todo_findings = [f for f in findings if f.rule == "todo-comment"]
        assert len(todo_findings) >= 1

    async def test_detects_mixed_indentation(self) -> None:
        content = "def f():\n \tx = 1\n"
        findings = await StyleAnalyzer().analyze(_make_file(content))
        mixed_findings = [f for f in findings if f.rule == "mixed-indentation"]
        assert len(mixed_findings) >= 1

    async def test_detects_superfluous_comment_python(self) -> None:
        content = "# import the module\nimport os\n"
        findings = await StyleAnalyzer().analyze(_make_file(content))
        sup_findings = [f for f in findings if f.rule == "superfluous-comment"]
        assert len(sup_findings) >= 1

    async def test_detects_superfluous_comment_js(self) -> None:
        content = "// import the library\nimport React from 'react';\n"
        findings = await StyleAnalyzer().analyze(
            _make_file(content, language="javascript", path="app.js")
        )
        sup_findings = [f for f in findings if f.rule == "superfluous-comment"]
        assert len(sup_findings) >= 1

    async def test_detects_camelcase_function_python(self) -> None:
        content = "def myFunction():\n    pass\n"
        findings = await StyleAnalyzer().analyze(_make_file(content))
        naming_findings = [f for f in findings if f.rule == "pep8-naming"]
        assert len(naming_findings) >= 1
        assert "camelCase" in naming_findings[0].message

    async def test_detects_lowercase_class_python(self) -> None:
        content = "class my_class:\n    pass\n"
        findings = await StyleAnalyzer().analyze(_make_file(content))
        naming_findings = [f for f in findings if f.rule == "pep8-naming"]
        assert len(naming_findings) >= 1
        assert "CapitalizedWords" in naming_findings[0].message

    async def test_detects_snake_case_function_js(self) -> None:
        content = "function my_function() { return 1; }\n"
        findings = await StyleAnalyzer().analyze(
            _make_file(content, language="javascript", path="app.js")
        )
        naming_findings = [f for f in findings if f.rule == "js-naming-convention"]
        assert len(naming_findings) >= 1

    async def test_clean_code_no_findings(self) -> None:
        content = "def greet(name):\n    return name\n"
        findings = await StyleAnalyzer().analyze(_make_file(content))
        assert len(findings) == 0

    async def test_todo_finding_includes_snippet(self) -> None:
        content = "x = 1  # TODO: refactor later\n"
        findings = await StyleAnalyzer().analyze(_make_file(content))
        todo_findings = [f for f in findings if f.rule == "todo-comment"]
        assert todo_findings[0].snippet is not None
