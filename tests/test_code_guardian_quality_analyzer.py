"""Tests for nasa_apod.services.code_guardian.analyzers.code_quality."""

import pytest

from nasa_apod.services.code_guardian.analyzers.code_quality import CodeQualityAnalyzer
from nasa_apod.services.code_guardian.models import ScannedFile


def _make_file(
    content: str, language: str = "python", path: str = "test.py", line_count: int | None = None
) -> list[ScannedFile]:
    """Wrap content in a single-file list for the analyzer."""
    lc = line_count if line_count is not None else content.count("\n") + 1
    return [ScannedFile(path=path, content=content, language=language, line_count=lc)]


@pytest.mark.asyncio
class TestCodeQualityAnalyzer:
    """Verify quality checks: file size, long lines, nesting, params."""

    async def test_name_and_category(self) -> None:
        analyzer = CodeQualityAnalyzer()
        assert analyzer.name == "code-quality-analyzer"
        assert analyzer.category == "quality"

    async def test_detects_large_file_over_500_lines(self) -> None:
        content = "x = 1\n" * 501
        findings = await CodeQualityAnalyzer().analyze(
            _make_file(content, line_count=501)
        )
        size_findings = [f for f in findings if f.rule == "file-too-large"]
        assert any(f.severity == "medium" for f in size_findings)

    async def test_detects_large_file_over_300_lines(self) -> None:
        content = "x = 1\n" * 301
        findings = await CodeQualityAnalyzer().analyze(
            _make_file(content, line_count=301)
        )
        size_findings = [f for f in findings if f.rule == "file-too-large"]
        assert any(f.severity == "low" for f in size_findings)

    async def test_no_size_finding_for_small_file(self) -> None:
        content = "x = 1\n" * 50
        findings = await CodeQualityAnalyzer().analyze(
            _make_file(content, line_count=50)
        )
        size_findings = [f for f in findings if f.rule == "file-too-large"]
        assert len(size_findings) == 0

    async def test_detects_long_lines(self) -> None:
        long_line = "x = " + "a" * 130 + "\n"
        findings = await CodeQualityAnalyzer().analyze(_make_file(long_line))
        line_findings = [f for f in findings if f.rule == "line-too-long"]
        assert len(line_findings) >= 1

    async def test_no_long_line_finding_for_short_lines(self) -> None:
        content = "x = 1\ny = 2\n"
        findings = await CodeQualityAnalyzer().analyze(_make_file(content))
        line_findings = [f for f in findings if f.rule == "line-too-long"]
        assert len(line_findings) == 0

    async def test_detects_deep_nesting_python(self) -> None:
        content = (
            "if True:\n"
            "    if True:\n"
            "        if True:\n"
            "            if True:\n"
            "                if True:\n"
            "                    x = 1\n"
        )
        findings = await CodeQualityAnalyzer().analyze(_make_file(content))
        nesting_findings = [f for f in findings if f.rule == "deep-nesting"]
        assert len(nesting_findings) >= 1

    async def test_detects_deep_nesting_brace_languages(self) -> None:
        content = "function f() {\n  if (x) {\n    if (y) {\n      if (z) {\n        if (w) {\n          x();\n        }\n      }\n    }\n  }\n}\n"
        findings = await CodeQualityAnalyzer().analyze(
            _make_file(content, language="javascript", path="app.js")
        )
        nesting_findings = [f for f in findings if f.rule == "deep-nesting"]
        assert len(nesting_findings) >= 1

    async def test_detects_too_many_params_python(self) -> None:
        content = "def func(a, b, c, d, e, f, g):\n    pass\n"
        findings = await CodeQualityAnalyzer().analyze(_make_file(content))
        param_findings = [f for f in findings if f.rule == "too-many-params"]
        assert len(param_findings) >= 1

    async def test_detects_too_many_params_js(self) -> None:
        content = "function doStuff(a, b, c, d, e, f, g) {\n  return a;\n}\n"
        findings = await CodeQualityAnalyzer().analyze(
            _make_file(content, language="javascript", path="app.js")
        )
        param_findings = [f for f in findings if f.rule == "too-many-params"]
        assert len(param_findings) >= 1

    async def test_no_param_finding_for_few_params(self) -> None:
        content = "def func(a, b):\n    pass\n"
        findings = await CodeQualityAnalyzer().analyze(_make_file(content))
        param_findings = [f for f in findings if f.rule == "too-many-params"]
        assert len(param_findings) == 0

    async def test_clean_small_file_no_findings(self) -> None:
        content = "x = 1\ny = 2\n"
        findings = await CodeQualityAnalyzer().analyze(
            _make_file(content, line_count=2)
        )
        assert len(findings) == 0
