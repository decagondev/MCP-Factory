"""Dependency vulnerability analyzer.

Parses common dependency manifest files (``package.json``,
``requirements.txt``, ``pyproject.toml``, ``Gemfile.lock``,
``go.mod``, ``Cargo.toml``) to extract package names, versions,
and ecosystems, then queries the OSV API for known
vulnerabilities.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from nasa_apod.services.code_guardian.analyzers import BaseAnalyzer
from nasa_apod.services.code_guardian.models import Finding, ScannedFile
from nasa_apod.services.code_guardian.osv_client import OsvClient

logger = logging.getLogger(__name__)

_MANIFEST_FILES: dict[str, str] = {
    "package.json": "npm",
    "requirements.txt": "PyPI",
    "pyproject.toml": "PyPI",
    "Gemfile.lock": "RubyGems",
    "go.mod": "Go",
    "Cargo.toml": "crates.io",
}
"""Mapping of manifest filenames to their OSV ecosystem identifiers."""


class DependencyAnalyzer(BaseAnalyzer):
    """Checks project dependencies for known CVEs via OSV.dev.

    Parses dependency manifests found in the scanned file set,
    extracts package names and versions, and queries the OSV API
    for each dependency.

    Args:
        osv_client: An :class:`OsvClient` instance for API calls.
    """

    def __init__(self, osv_client: OsvClient) -> None:
        self._client = osv_client

    @property
    def name(self) -> str:
        """Returns ``"dependency-analyzer"``."""
        return "dependency-analyzer"

    @property
    def category(self) -> str:
        """Returns ``"vulnerability"``."""
        return "vulnerability"

    async def analyze(self, files: list[ScannedFile]) -> list[Finding]:
        """Parse manifests and query OSV for each dependency.

        Args:
            files: Pre-scanned source files (may include manifests).

        Returns:
            Findings for each dependency with known vulnerabilities.
        """
        findings: list[Finding] = []

        for scanned in files:
            filename = scanned.path.rsplit("/", maxsplit=1)[-1]
            if filename not in _MANIFEST_FILES:
                filename_backslash = scanned.path.rsplit("\\", maxsplit=1)[-1]
                if filename_backslash not in _MANIFEST_FILES:
                    continue
                filename = filename_backslash

            ecosystem = _MANIFEST_FILES[filename]
            deps = self._parse_dependencies(scanned.content, filename, ecosystem)

            for dep_name, dep_version in deps:
                vuln_findings = await self._check_dependency(
                    dep_name, dep_version, ecosystem, scanned.path
                )
                findings.extend(vuln_findings)

        return findings

    async def _check_dependency(
        self,
        name: str,
        version: str,
        ecosystem: str,
        manifest_path: str,
    ) -> list[Finding]:
        """Query OSV for a single dependency and return findings.

        Args:
            name: Package name.
            version: Package version string.
            ecosystem: OSV ecosystem identifier.
            manifest_path: Path to the manifest for finding context.

        Returns:
            One finding per vulnerability advisory, or empty on
            clean/error.
        """
        params: dict[str, str] = {"name": name, "ecosystem": ecosystem}
        if version:
            params["version"] = version

        data = await self._client.fetch(**params)
        if data is None:
            return []

        vulns: list[dict[str, Any]] = data.get("vulns", [])
        findings: list[Finding] = []

        for vuln in vulns:
            vuln_id = vuln.get("id", "unknown")
            summary = vuln.get("summary", "No summary available")
            severity = self._determine_severity(vuln)

            findings.append(
                Finding(
                    severity=severity,
                    category="vulnerability",
                    rule="known-vulnerability",
                    message=f"{vuln_id}: {summary} (package: {name}@{version or 'any'})",
                    file_path=manifest_path,
                )
            )

        return findings

    @staticmethod
    def _determine_severity(vuln: dict[str, Any]) -> str:
        """Map OSV severity data to our severity levels.

        Args:
            vuln: A single vulnerability record from the OSV API.

        Returns:
            One of ``"critical"``, ``"high"``, ``"medium"``, or
            ``"low"``.
        """
        severity_entries = vuln.get("severity", [])
        for entry in severity_entries:
            score_str = entry.get("score", "")
            try:
                score = float(score_str)
            except (ValueError, TypeError):
                continue
            if score >= 9.0:
                return "critical"
            if score >= 7.0:
                return "high"
            if score >= 4.0:
                return "medium"
            return "low"

        database_specific = vuln.get("database_specific", {})
        osv_severity = database_specific.get("severity", "").upper()
        if osv_severity in {"CRITICAL"}:
            return "critical"
        if osv_severity in {"HIGH"}:
            return "high"
        if osv_severity in {"MODERATE", "MEDIUM"}:
            return "medium"

        return "high"

    @staticmethod
    def _parse_dependencies(
        content: str, filename: str, ecosystem: str
    ) -> list[tuple[str, str]]:
        """Extract (name, version) pairs from a manifest.

        Args:
            content: Raw file content.
            filename: The manifest filename.
            ecosystem: The OSV ecosystem identifier.

        Returns:
            List of (package_name, version_string) tuples.
        """
        if filename == "package.json":
            return DependencyAnalyzer._parse_package_json(content)
        if filename == "requirements.txt":
            return DependencyAnalyzer._parse_requirements_txt(content)
        if filename == "pyproject.toml":
            return DependencyAnalyzer._parse_pyproject_toml(content)
        if filename == "go.mod":
            return DependencyAnalyzer._parse_go_mod(content)
        if filename == "Cargo.toml":
            return DependencyAnalyzer._parse_cargo_toml(content)
        if filename == "Gemfile.lock":
            return DependencyAnalyzer._parse_gemfile_lock(content)
        return []

    @staticmethod
    def _parse_package_json(content: str) -> list[tuple[str, str]]:
        """Parse package.json dependencies.

        Args:
            content: Raw JSON content.

        Returns:
            List of (name, version) tuples.
        """
        deps: list[tuple[str, str]] = []
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return deps
        for section in ("dependencies", "devDependencies"):
            for name, version in data.get(section, {}).items():
                clean_version = re.sub(r"^[~^>=<]+", "", version)
                deps.append((name, clean_version))
        return deps

    @staticmethod
    def _parse_requirements_txt(content: str) -> list[tuple[str, str]]:
        """Parse requirements.txt dependencies.

        Args:
            content: Raw text content.

        Returns:
            List of (name, version) tuples.
        """
        deps: list[tuple[str, str]] = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith(("#", "-")):
                continue
            match = re.match(r"^([A-Za-z0-9_\-.]+)\s*(?:[>=<~!]+\s*(.+))?", line)
            if match:
                name = match.group(1)
                version = (match.group(2) or "").split(",")[0].strip()
                deps.append((name, version))
        return deps

    @staticmethod
    def _parse_pyproject_toml(content: str) -> list[tuple[str, str]]:
        """Parse pyproject.toml dependencies (simplified regex).

        Args:
            content: Raw TOML content.

        Returns:
            List of (name, version) tuples.
        """
        deps: list[tuple[str, str]] = []
        in_deps = False
        for line in content.splitlines():
            stripped = line.strip()
            if re.match(r"^\[.*dependencies.*\]", stripped, re.IGNORECASE):
                in_deps = True
                continue
            if stripped.startswith("[") and in_deps:
                in_deps = False
                continue
            if in_deps and stripped.startswith('"'):
                match = re.match(r'"([A-Za-z0-9_\-. ]+)(?:[>=<~!]+(.+))?"', stripped)
                if match:
                    name = match.group(1).strip()
                    version = (match.group(2) or "").strip().rstrip('"').rstrip(",")
                    deps.append((name, version))
            elif in_deps and "=" in stripped:
                match = re.match(r"([A-Za-z0-9_\-.]+)\s*=", stripped)
                if match:
                    deps.append((match.group(1), ""))
        return deps

    @staticmethod
    def _parse_go_mod(content: str) -> list[tuple[str, str]]:
        """Parse go.mod require directives.

        Args:
            content: Raw go.mod content.

        Returns:
            List of (module_path, version) tuples.
        """
        deps: list[tuple[str, str]] = []
        in_require = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("require ("):
                in_require = True
                continue
            if in_require and stripped == ")":
                in_require = False
                continue
            if in_require:
                parts = stripped.split()
                if len(parts) >= 2:
                    deps.append((parts[0], parts[1].lstrip("v")))
            elif stripped.startswith("require "):
                parts = stripped.split()
                if len(parts) >= 3:
                    deps.append((parts[1], parts[2].lstrip("v")))
        return deps

    @staticmethod
    def _parse_cargo_toml(content: str) -> list[tuple[str, str]]:
        """Parse Cargo.toml [dependencies] section (simplified).

        Args:
            content: Raw TOML content.

        Returns:
            List of (crate_name, version) tuples.
        """
        deps: list[tuple[str, str]] = []
        in_deps = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped == "[dependencies]":
                in_deps = True
                continue
            if stripped.startswith("[") and in_deps:
                in_deps = False
                continue
            if in_deps and "=" in stripped:
                match = re.match(r'([A-Za-z0-9_\-]+)\s*=\s*"([^"]*)"', stripped)
                if match:
                    deps.append((match.group(1), match.group(2)))
                else:
                    key_match = re.match(r"([A-Za-z0-9_\-]+)\s*=", stripped)
                    if key_match:
                        deps.append((key_match.group(1), ""))
        return deps

    @staticmethod
    def _parse_gemfile_lock(content: str) -> list[tuple[str, str]]:
        """Parse Gemfile.lock specs section.

        Args:
            content: Raw Gemfile.lock content.

        Returns:
            List of (gem_name, version) tuples.
        """
        deps: list[tuple[str, str]] = []
        in_specs = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped == "specs:":
                in_specs = True
                continue
            if in_specs and not line.startswith(" "):
                in_specs = False
                continue
            if in_specs:
                match = re.match(r"(\S+)\s+\(([^)]+)\)", stripped)
                if match:
                    deps.append((match.group(1), match.group(2)))
        return deps
