"""Analyzer framework for the Code Guardian service.

Provides the :class:`BaseAnalyzer` abstract base class that every
concrete analyzer must extend, and the :class:`AnalyzerRegistry`
that collects analyzers and orchestrates multi-pass scans.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from nasa_apod.services.code_guardian.models import Finding, ScanResult, ScannedFile

logger = logging.getLogger(__name__)

__all__ = ["BaseAnalyzer", "AnalyzerRegistry"]


class BaseAnalyzer(ABC):
    """Contract for all Code Guardian analyzers.

    Each analyzer inspects a list of scanned files and returns
    findings.  The :pyattr:`name` property is used for logging
    and the ``analyzers_run`` field of :class:`ScanResult`.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Machine-readable identifier for this analyzer.

        Returns:
            A short, unique string such as ``"secret-scanner"``.
        """

    @property
    def category(self) -> str:
        """Broad classification for findings produced by this analyzer.

        Defaults to ``"general"``; subclasses should override to
        return ``"security"``, ``"quality"``, ``"style"``, or
        ``"vulnerability"``.

        Returns:
            Category string used in :class:`Finding` objects.
        """
        return "general"

    @abstractmethod
    async def analyze(self, files: list[ScannedFile]) -> list[Finding]:
        """Run this analyzer over the given source files.

        Args:
            files: Pre-scanned source files to inspect.

        Returns:
            A list of findings (may be empty).
        """


class AnalyzerRegistry:
    """Collects :class:`BaseAnalyzer` instances and orchestrates scans.

    Usage::

        registry = AnalyzerRegistry()
        registry.add(SecretAnalyzer())
        registry.add(StyleAnalyzer())
        result = await registry.run_all(files)
    """

    def __init__(self) -> None:
        self._analyzers: list[BaseAnalyzer] = []

    def add(self, analyzer: BaseAnalyzer) -> None:
        """Register an analyzer for use in subsequent scans.

        Args:
            analyzer: Any concrete :class:`BaseAnalyzer` subclass.
        """
        self._analyzers.append(analyzer)
        logger.info("Registered analyzer: %s", analyzer.name)

    @property
    def analyzers(self) -> list[BaseAnalyzer]:
        """Read-only snapshot of registered analyzers."""
        return list(self._analyzers)

    async def run_all(self, files: list[ScannedFile]) -> ScanResult:
        """Execute every registered analyzer and aggregate results.

        Args:
            files: Source files to analyze.

        Returns:
            A :class:`ScanResult` containing merged findings from all
            analyzers.
        """
        all_findings: list[Finding] = []
        names: list[str] = []

        for analyzer in self._analyzers:
            logger.info("Running analyzer: %s", analyzer.name)
            findings = await analyzer.analyze(files)
            all_findings.extend(findings)
            names.append(analyzer.name)

        return ScanResult(
            findings=all_findings,
            files_scanned=len(files),
            analyzers_run=names,
        )

    async def run_by_category(
        self, category: str, files: list[ScannedFile]
    ) -> ScanResult:
        """Execute only analyzers matching *category*.

        Args:
            category: The category string to match
                      (e.g. ``"security"``).
            files: Source files to analyze.

        Returns:
            A :class:`ScanResult` from the matching analyzers only.
        """
        all_findings: list[Finding] = []
        names: list[str] = []

        for analyzer in self._analyzers:
            if analyzer.category != category:
                continue
            logger.info("Running analyzer: %s", analyzer.name)
            findings = await analyzer.analyze(files)
            all_findings.extend(findings)
            names.append(analyzer.name)

        return ScanResult(
            findings=all_findings,
            files_scanned=len(files),
            analyzers_run=names,
        )
