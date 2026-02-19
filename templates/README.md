# Service Templates

This directory contains a copy-paste-ready service plugin skeleton. Use it to create a new API service without starting from scratch.

## Usage

### Option A: Copy and rename (recommended)

```bash
cp -r templates/service_template mcp_factory/services/your_service_name
```

Then open each file in the new directory and replace the `TODO` placeholders with your domain-specific logic.

### Option B: Manual creation

Use the templates as a reference while creating files from scratch. Each template shows the correct imports, class signatures, and method contracts.

## Template Files

| File | Contains | Customize |
|------|----------|-----------|
| `__init__.py` | Service class with `register(mcp)` method | Add your tools and resources |
| `config.py` | Configuration constants | Set your API URL, env var name, timeout |
| `client.py` | HTTP client extending `BaseAPIClient` | Implement your `fetch()` logic |
| `formatter.py` | Formatter extending `BaseFormatter` | Implement your `format()` logic |
| `validation.py` | Input validation function | Add your domain-specific validation |

## After Copying

1. Replace all `TODO` markers with your implementation
2. Rename classes from `TemplateClient` / `TemplateFormatter` / `TemplateService` to match your API
3. Register the service in `mcp_factory/server.py`:
   ```python
   from mcp_factory.services.your_service_name import YourService
   registry.add(YourService())
   ```
4. Write tests (see `tests/test_apod_*.py` for patterns)
5. Run `uv run pytest -v` to verify

## Reference Implementation

The APOD service at `mcp_factory/services/apod/` is a complete working implementation of this template pattern.
