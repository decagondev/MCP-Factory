# MCP Factory

An extensible [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server framework with a **service plugin architecture**. Built with [FastMCP](https://github.com/jlowin/fastmcp) and Python 3.13. Ships with a NASA APOD (Astronomy Picture of the Day) service as a reference implementation.

Add new API services by implementing a plugin -- your tools appear automatically in every MCP client. Fork the repo to build your own production MCP server from a solid, SOLID foundation.

## Bundled Service: NASA APOD

The included APOD service demonstrates the plugin pattern with these features:

- **Get Today's Photo** — Fetch the current Astronomy Picture of the Day with title, explanation, and media link.
- **Get Photo by Date** — Retrieve any APOD entry from the archive (1995-06-16 to today) by providing a date.
- **Get Random Photo** — Discover a random APOD from NASA's 30+ year archive.
- **Famous Space Dates Resource** — A curated list of iconic space exploration dates to explore in the APOD archive.

## Tools

| Tool | Description |
|------|-------------|
| `get_todays_space_photo` | Returns today's APOD with title, explanation, media type, and URL |
| `get_space_photo_by_date` | Returns the APOD for a specific date (`YYYY-MM-DD` format) |
| `get_random_space_photo` | Returns a random APOD from the full archive |

## Resources

| URI | Description |
|-----|-------------|
| `space://events/famous-dates` | Curated list of famous space exploration dates |

## Prerequisites

- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) (recommended package manager)

## Installation

```bash
git clone <your-repo-url>
cd mcp-factory
uv sync
```

## Usage

### Running the server standalone

```bash
uv run main.py
```

The server communicates over **stdio** transport, which is the standard for MCP client integrations.

### Adding to Cursor IDE

Add the following to your Cursor MCP settings (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "mcp-factory": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/mcp-factory",
        "main.py"
      ]
    }
  }
}
```

Replace `/absolute/path/to/mcp-factory` with the actual path to this project on your machine.

### Adding to Claude Desktop

Add the following to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mcp-factory": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/mcp-factory",
        "main.py"
      ]
    }
  }
}
```

## API Key

The bundled APOD service uses NASA's `DEMO_KEY` by default, which has limited rate limits (30 requests/hour, 50 requests/day per IP). For heavier usage, [request a free API key](https://api.nasa.gov/) and set the `NASA_API_KEY` environment variable:

```bash
export NASA_API_KEY="your-key-here"
```

## Project Structure

```
mcp-factory/
├── main.py                         # Thin entry point — starts the MCP server
├── mcp_factory/                      # Core package
│   ├── __init__.py
│   ├── config.py                   # Global config (server name)
│   ├── server.py                   # Builds FastMCP via ServiceRegistry
│   └── services/                   # Service plugin architecture
│       ├── __init__.py
│       ├── base.py                 # ABCs: BaseAPIClient, BaseFormatter, ServicePlugin
│       ├── registry.py             # ServiceRegistry factory
│       └── apod/                   # APOD service plugin
│           ├── __init__.py         # ApodService (registers tools + resources)
│           ├── config.py           # APOD-specific constants and API key
│           ├── client.py           # ApodClient (extends BaseAPIClient)
│           ├── formatter.py        # ApodFormatter (extends BaseFormatter)
│           └── validation.py       # APOD date validation
├── tests/                          # Unit + E2E tests (pytest)
│   ├── test_base.py                # ABC contract tests
│   ├── test_registry.py            # ServiceRegistry factory tests
│   ├── test_apod_config.py         # APOD config constants
│   ├── test_apod_client.py         # ApodClient with mocked HTTP
│   ├── test_apod_formatter.py      # ApodFormatter output
│   ├── test_apod_validation.py     # Date validation
│   └── test_e2e.py                 # Full server bootstrap + tool execution
├── templates/                      # Copy-paste service boilerplate
│   ├── README.md                   # Template usage instructions
│   └── service_template/           # Complete service plugin skeleton
├── docs/                           # Guides, architecture, and workshop
│   ├── ARCHITECTURE.md             # System design and SOLID mapping
│   ├── ADDING-A-SERVICE.md         # Step-by-step new service guide
│   ├── ADDING-TOOLS.md             # Tool and resource creation guide
│   ├── FORKING-GUIDE.md            # Using this repo as a template
│   ├── DEVELOPMENT-WORKFLOW.md     # Git, testing, and review workflow
│   ├── LETS-BUILD-AN-MCP-SERVER.md # Original step-by-step tutorial
│   └── index.html                  # Slide deck presentation
├── CLAUDE.md                       # AI agent context (Claude Code, etc.)
├── pyproject.toml                  # Project metadata and dependencies
├── uv.lock                         # Locked dependency versions
├── .python-version                 # Python version (3.13)
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## Extending with a New API Service

This server uses a **service plugin architecture**. Each API is a self-contained plugin under `mcp_factory/services/`. To add a new API:

1. Create a new directory: `mcp_factory/services/your_api/`
2. Implement a client extending `BaseAPIClient` (handles HTTP)
3. Implement a formatter extending `BaseFormatter` (handles Markdown output)
4. Create a service class with a `register(mcp)` method that registers your tools
5. Add it to the registry in `mcp_factory/server.py`:

```python
from mcp_factory.services.your_api import YourApiService

registry.add(YourApiService())
```

Your new tools appear automatically -- no other files need to change.

## Documentation

### For Developers

| Guide | Description |
|-------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design, plugin lifecycle, data flow, SOLID principles, module map |
| [Adding a Service](docs/ADDING-A-SERVICE.md) | Step-by-step guide to adding a new API service plugin |
| [Adding Tools](docs/ADDING-TOOLS.md) | How to add tools and resources to an existing service |
| [Forking Guide](docs/FORKING-GUIDE.md) | Using this repo as a template for a new MCP server |
| [Development Workflow](docs/DEVELOPMENT-WORKFLOW.md) | Git workflow, testing strategy, code review checklist |
| [Tutorial](docs/LETS-BUILD-AN-MCP-SERVER.md) | Original step-by-step MCP server tutorial |

### For AI Agents

| Resource | Description |
|----------|-------------|
| [CLAUDE.md](CLAUDE.md) | Root-level context file for Claude Code and agentic frameworks |
| `.cursor/rules/architecture.mdc` | Always-on architecture context for Cursor AI |
| `.cursor/rules/extending-services.mdc` | Step-by-step instructions triggered when extending services |
| `.cursor/rules/mcp-factory-tools.mdc` | Tool routing rules for bundled APOD service |

### Boilerplate Templates

Copy-paste-ready service skeleton at `templates/service_template/`. See [templates/README.md](templates/README.md) for usage.

## Dependencies

- **[mcp[cli]](https://pypi.org/project/mcp/)** — Model Context Protocol SDK with CLI support
- **[httpx](https://www.python-httpx.org/)** — Async HTTP client for external API calls

## License

This project is for educational and personal use. The bundled APOD service uses data from [NASA's APOD API](https://api.nasa.gov/).
