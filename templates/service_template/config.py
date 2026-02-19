"""Configuration constants for the TODO: <Service Name> service.

All values specific to this API live here. Global/shared settings
remain in ``mcp_factory.config``.

TODO: Replace placeholder values with your API's configuration.
"""

import os

API_BASE_URL: str = "https://api.example.com/v1/endpoint"
"""TODO: Set the base URL for your API endpoint."""

API_KEY: str = os.environ.get("TODO_YOUR_API_KEY", "")
"""TODO: Set the environment variable name for your API key.

Load the key from an environment variable. Never hardcode secrets.
"""

REQUEST_TIMEOUT_SECONDS: float = 30.0
"""HTTP request timeout in seconds. Adjust based on your API's response time."""
