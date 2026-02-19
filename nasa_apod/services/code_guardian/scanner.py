"""File scanner for the Code Guardian service.

Walks a directory tree, filters out ignored paths, reads source
files within size limits, and produces a list of
:class:`~nasa_apod.services.code_guardian.models.ScannedFile` objects
ready for analysis.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from nasa_apod.services.code_guardian.config import (
    IGNORE_DIRECTORIES,
    MAX_FILE_SIZE_BYTES,
    SUPPORTED_EXTENSIONS,
)
from nasa_apod.services.code_guardian.models import ScannedFile

logger = logging.getLogger(__name__)


class FileScanner:
    """Recursively scans a directory and yields analysable source files.

    Respects ``IGNORE_DIRECTORIES``, ``SUPPORTED_EXTENSIONS``, and
    ``MAX_FILE_SIZE_BYTES`` from the service configuration so that
    binary blobs, dependency caches, and unsupported formats are
    silently skipped.

    Args:
        root: Absolute path to the directory to scan.
        supported_extensions: Override the default extension map.
        ignore_dirs: Override the default ignored-directory set.
        max_file_bytes: Override the default size cap.
    """

    def __init__(
        self,
        root: str,
        *,
        supported_extensions: dict[str, str] | None = None,
        ignore_dirs: set[str] | None = None,
        max_file_bytes: int = MAX_FILE_SIZE_BYTES,
    ) -> None:
        self.root = root
        self._extensions = supported_extensions or SUPPORTED_EXTENSIONS
        self._ignore_dirs = ignore_dirs or IGNORE_DIRECTORIES
        self._max_bytes = max_file_bytes

    def _detect_language(self, file_path: str) -> str | None:
        """Resolve the canonical language name for a file extension.

        Args:
            file_path: Path (or filename) whose suffix is checked.

        Returns:
            Language string when the extension is supported, else
            ``None``.
        """
        ext = Path(file_path).suffix.lower()
        return self._extensions.get(ext)

    def _should_ignore_dir(self, dir_name: str) -> bool:
        """Decide whether a directory should be skipped entirely.

        Args:
            dir_name: The directory's base name (not the full path).

        Returns:
            ``True`` when the name appears in the ignore set.
        """
        return dir_name in self._ignore_dirs

    async def scan(self) -> list[ScannedFile]:
        """Walk the root tree and return every scannable source file.

        Files are skipped when they:
        - reside inside an ignored directory,
        - have an unsupported extension,
        - exceed ``max_file_bytes``, or
        - cannot be decoded as UTF-8.

        Returns:
            A list of :class:`ScannedFile` instances.
        """
        results: list[ScannedFile] = []

        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [
                d for d in dirnames if not self._should_ignore_dir(d)
            ]

            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                language = self._detect_language(filename)
                if language is None:
                    continue

                try:
                    file_size = os.path.getsize(full_path)
                except OSError:
                    logger.warning("Cannot stat file: %s", full_path)
                    continue

                if file_size > self._max_bytes:
                    logger.info(
                        "Skipping oversized file (%d bytes): %s",
                        file_size,
                        full_path,
                    )
                    continue

                try:
                    with open(full_path, encoding="utf-8") as fh:
                        content = fh.read()
                except (OSError, UnicodeDecodeError) as exc:
                    logger.warning("Cannot read file %s: %s", full_path, exc)
                    continue

                rel_path = os.path.relpath(full_path, self.root)
                line_count = content.count("\n") + (
                    1 if content and not content.endswith("\n") else 0
                )

                results.append(
                    ScannedFile(
                        path=rel_path,
                        content=content,
                        language=language,
                        line_count=line_count,
                    )
                )

        return results
