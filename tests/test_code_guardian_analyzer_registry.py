"""Tests for the BaseAnalyzer ABC and AnalyzerRegistry."""

import pytest

from nasa_apod.services.code_guardian.analyzers import BaseAnalyzer, AnalyzerRegistry
from nasa_apod.services.code_guardian.models import Finding, ScannedFile


class _StubAnalyzer(BaseAnalyzer):
    """Minimal concrete analyzer for testing the registry."""

    def __init__(self, analyzer_name: str, cat: str, findings: list[Finding] | None = None) -> None:
        self._name = analyzer_name
        self._category = cat
        self._findings = findings or []

    @property
    def name(self) -> str:
        return self._name

    @property
    def category(self) -> str:
        return self._category

    async def analyze(self, files: list[ScannedFile]) -> list[Finding]:
        return self._findings


DUMMY_FILES: list[ScannedFile] = [
    ScannedFile(path="a.py", content="pass\n", language="python", line_count=1),
]


class TestBaseAnalyzer:
    """Verify the ABC cannot be instantiated directly."""

    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError):
            BaseAnalyzer()  # type: ignore[abstract]

    def test_default_category_is_general(self) -> None:
        stub = _StubAnalyzer("test", "general")
        assert stub.category == "general"


@pytest.mark.asyncio
class TestAnalyzerRegistry:
    """Verify registration, ordering, and orchestration."""

    async def test_add_and_list_analyzers(self) -> None:
        registry = AnalyzerRegistry()
        a1 = _StubAnalyzer("first", "security")
        a2 = _StubAnalyzer("second", "quality")
        registry.add(a1)
        registry.add(a2)
        assert [a.name for a in registry.analyzers] == ["first", "second"]

    async def test_run_all_merges_findings(self) -> None:
        f1 = Finding(severity="high", category="security", rule="r1", message="m1", file_path="a.py")
        f2 = Finding(severity="low", category="quality", rule="r2", message="m2", file_path="b.py")

        registry = AnalyzerRegistry()
        registry.add(_StubAnalyzer("sec", "security", [f1]))
        registry.add(_StubAnalyzer("qual", "quality", [f2]))

        result = await registry.run_all(DUMMY_FILES)
        assert len(result.findings) == 2
        assert result.files_scanned == 1
        assert result.analyzers_run == ["sec", "qual"]

    async def test_run_by_category_filters(self) -> None:
        f1 = Finding(severity="high", category="security", rule="r1", message="m1", file_path="a.py")
        f2 = Finding(severity="low", category="quality", rule="r2", message="m2", file_path="b.py")

        registry = AnalyzerRegistry()
        registry.add(_StubAnalyzer("sec", "security", [f1]))
        registry.add(_StubAnalyzer("qual", "quality", [f2]))

        result = await registry.run_by_category("security", DUMMY_FILES)
        assert len(result.findings) == 1
        assert result.findings[0].rule == "r1"
        assert result.analyzers_run == ["sec"]

    async def test_run_all_with_no_analyzers(self) -> None:
        registry = AnalyzerRegistry()
        result = await registry.run_all(DUMMY_FILES)
        assert result.findings == []
        assert result.analyzers_run == []

    async def test_run_by_category_with_no_match(self) -> None:
        registry = AnalyzerRegistry()
        registry.add(_StubAnalyzer("sec", "security"))
        result = await registry.run_by_category("quality", DUMMY_FILES)
        assert result.findings == []
        assert result.analyzers_run == []
