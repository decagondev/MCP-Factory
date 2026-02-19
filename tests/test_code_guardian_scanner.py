"""Tests for mcp_factory.services.code_guardian.scanner."""

import os
import tempfile

import pytest

from mcp_factory.services.code_guardian.scanner import FileScanner


def _create_tree(base: str, structure: dict[str, str | dict]) -> None:
    """Recursively create files and directories under *base*.

    Args:
        base: Root directory.
        structure: Mapping of names to content strings (files) or
                   nested dicts (subdirectories).
    """
    for name, value in structure.items():
        path = os.path.join(base, name)
        if isinstance(value, dict):
            os.makedirs(path, exist_ok=True)
            _create_tree(path, value)
        else:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(value)


@pytest.mark.asyncio
class TestFileScanner:
    """Verify directory walking, filtering, and language detection."""

    async def test_scans_supported_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _create_tree(tmp, {
                "app.py": "x = 1\n",
                "index.js": "const a = 1;\n",
            })
            scanner = FileScanner(tmp)
            files = await scanner.scan()
            paths = {f.path for f in files}
            assert "app.py" in paths
            assert "index.js" in paths

    async def test_ignores_unsupported_extensions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _create_tree(tmp, {"photo.png": "binary", "data.bin": "binary"})
            scanner = FileScanner(tmp)
            files = await scanner.scan()
            assert len(files) == 0

    async def test_ignores_configured_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _create_tree(tmp, {
                "src": {"main.py": "pass\n"},
                "node_modules": {"dep.js": "module.exports = {};\n"},
                "__pycache__": {"cached.py": "cached\n"},
            })
            scanner = FileScanner(tmp)
            files = await scanner.scan()
            paths = {f.path for f in files}
            assert any("main.py" in p for p in paths)
            assert not any("node_modules" in p for p in paths)
            assert not any("__pycache__" in p for p in paths)

    async def test_detects_language_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _create_tree(tmp, {
                "app.ts": "const x: number = 1;\n",
                "Main.java": "class Main {}\n",
                "lib.rs": "fn main() {}\n",
            })
            scanner = FileScanner(tmp)
            files = await scanner.scan()
            lang_map = {f.path: f.language for f in files}
            assert lang_map["app.ts"] == "typescript"
            assert lang_map["Main.java"] == "java"
            assert lang_map["lib.rs"] == "rust"

    async def test_counts_lines_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _create_tree(tmp, {"three_lines.py": "a\nb\nc\n"})
            scanner = FileScanner(tmp)
            files = await scanner.scan()
            assert files[0].line_count == 3

    async def test_skips_oversized_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _create_tree(tmp, {"big.py": "x" * 200})
            scanner = FileScanner(tmp, max_file_bytes=100)
            files = await scanner.scan()
            assert len(files) == 0

    async def test_handles_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scanner = FileScanner(tmp)
            files = await scanner.scan()
            assert files == []

    async def test_uses_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _create_tree(tmp, {"sub": {"deep.py": "pass\n"}})
            scanner = FileScanner(tmp)
            files = await scanner.scan()
            assert files[0].path == os.path.join("sub", "deep.py")

    async def test_skips_binary_files_gracefully(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = os.path.join(tmp, "bad.py")
            with open(bad_path, "wb") as fh:
                fh.write(b"\x80\x81\x82\x83")
            scanner = FileScanner(tmp)
            files = await scanner.scan()
            assert len(files) == 0
