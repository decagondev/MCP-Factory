"""Tests for nasa_apod.services.apod.validation."""

from datetime import datetime

import pytest

from nasa_apod.services.apod.validation import validate_apod_date


class TestValidateApodDate:
    """Cover the four possible outcomes of date validation."""

    def test_valid_date_returns_datetime(self) -> None:
        result = validate_apod_date("2020-07-04")
        assert isinstance(result, datetime)
        assert result == datetime(2020, 7, 4)

    def test_first_apod_date_is_accepted(self) -> None:
        result = validate_apod_date("1995-06-16")
        assert isinstance(result, datetime)

    def test_invalid_format_returns_error_string(self) -> None:
        result = validate_apod_date("07/04/2020")
        assert isinstance(result, str)
        assert "YYYY-MM-DD" in result

    def test_empty_string_returns_error(self) -> None:
        result = validate_apod_date("")
        assert isinstance(result, str)

    def test_date_before_first_apod_returns_error(self) -> None:
        result = validate_apod_date("1990-01-01")
        assert isinstance(result, str)
        assert "1995-06-16" in result

    def test_future_date_returns_error(self) -> None:
        result = validate_apod_date("2099-12-31")
        assert isinstance(result, str)
        assert "today" in result
