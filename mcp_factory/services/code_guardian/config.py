"""Code Guardian service configuration constants.

Centralises every tunable value for file scanning, severity
classification, and language detection.  Service-wide settings
remain in ``mcp_factory.config``; only Code-Guardian-specific
constants belong here.
"""

OSV_API_BASE_URL: str = "https://api.osv.dev/v1"
"""Base URL for the Open Source Vulnerabilities REST API."""

OSV_API_KEY: str = ""
"""OSV requires no authentication; kept for BaseAPIClient compat."""

OSV_REQUEST_TIMEOUT_SECONDS: float = 30.0
"""HTTP request timeout in seconds for OSV API calls."""

SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "shell",
    ".bash": "shell",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".md": "markdown",
    ".txt": "text",
    ".cfg": "config",
    ".ini": "config",
    ".env": "dotenv",
}
"""Map of file extensions to canonical language names."""

IGNORE_DIRECTORIES: set[str] = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    "vendor",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "coverage",
    ".idea",
    ".vscode",
}
"""Directory names skipped during recursive file scanning."""

MAX_FILE_SIZE_BYTES: int = 1_048_576
"""Skip files larger than 1 MiB to avoid memory pressure."""

FILE_SIZE_WARN_LINES: int = 300
"""Line count above which a file receives a *medium* quality warning."""

FILE_SIZE_ERROR_LINES: int = 500
"""Line count above which a file receives a *high* quality warning."""

LINE_LENGTH_LIMIT: int = 120
"""Maximum recommended characters per source line."""

MAX_NESTING_DEPTH: int = 4
"""Brace/indent nesting depth above which a quality warning fires."""

MAX_FUNCTION_PARAMS: int = 5
"""Parameter count above which a quality warning fires."""

SEVERITY_LEVELS: tuple[str, ...] = (
    "critical",
    "high",
    "medium",
    "low",
    "info",
)
"""Ordered severity levels from most to least severe."""
