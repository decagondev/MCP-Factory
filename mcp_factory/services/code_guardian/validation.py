"""Input validation for Code Guardian tool parameters.

Isolates path-checking and option-validation logic so that tool
functions remain thin orchestrators.
"""

from __future__ import annotations

import os


def validate_scan_path(path: str) -> str | None:
    """Validate that *path* points to a readable directory.

    Args:
        path: Filesystem path provided by the user.

    Returns:
        A human-readable error string when the path is invalid,
        or ``None`` when validation passes.
    """
    if not path or not path.strip():
        return "Path must not be empty."

    expanded = os.path.expanduser(path.strip())

    if not os.path.exists(expanded):
        return f"Path does not exist: {expanded}"

    if not os.path.isdir(expanded):
        return f"Path is not a directory: {expanded}"

    if not os.access(expanded, os.R_OK):
        return f"Path is not readable: {expanded}"

    return None
