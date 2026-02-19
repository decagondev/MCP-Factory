"""Input validation for the TODO: <Service Name> service.

Isolates all input-parsing and validation logic so that tool functions
stay thin orchestrators and validation rules live in exactly one place.

TODO: Implement validation functions for your service's input parameters.
This file is optional -- only include it if your service needs input
validation beyond basic type checking.
"""


def validate_input(value: str) -> str | None:
    """Validate a user-provided input string.

    TODO: Replace this with your domain-specific validation logic.

    Args:
        value: The raw input string to validate.

    Returns:
        ``None`` on success (input is valid), or a human-readable
        error message string when validation fails.
    """
    if not value.strip():
        return "Input cannot be empty."

    return None
