"""Tests for mcp_factory.services.apod.formatter."""

from mcp_factory.services.apod.formatter import ApodFormatter

SAMPLE_DATA: dict = {
    "title": "The Milky Way over Bryce Canyon",
    "date": "2024-03-15",
    "explanation": "A stunning panorama of the Milky Way arching over Bryce Canyon.",
    "media_type": "image",
    "url": "https://apod.nasa.gov/apod/image/2403/BryceCanyon.jpg",
}


class TestApodFormatter:
    """Verify the Markdown output structure for various data shapes."""

    def setup_method(self) -> None:
        self.formatter = ApodFormatter()

    def test_includes_title(self) -> None:
        result = self.formatter.format(SAMPLE_DATA)
        assert SAMPLE_DATA["title"] in result

    def test_includes_date(self) -> None:
        result = self.formatter.format(SAMPLE_DATA)
        assert SAMPLE_DATA["date"] in result

    def test_includes_explanation(self) -> None:
        result = self.formatter.format(SAMPLE_DATA)
        assert SAMPLE_DATA["explanation"] in result

    def test_includes_media_type_title_cased(self) -> None:
        result = self.formatter.format(SAMPLE_DATA)
        assert "Image" in result

    def test_includes_url(self) -> None:
        result = self.formatter.format(SAMPLE_DATA)
        assert SAMPLE_DATA["url"] in result

    def test_copyright_shown_when_present(self) -> None:
        data_with_copyright = {**SAMPLE_DATA, "copyright": "Jane Astronomer"}
        result = self.formatter.format(data_with_copyright)
        assert "Jane Astronomer" in result

    def test_no_copyright_line_when_absent(self) -> None:
        result = self.formatter.format(SAMPLE_DATA)
        assert "Copyright" not in result

    def test_header_prepended_when_provided(self) -> None:
        result = self.formatter.format(SAMPLE_DATA, header="** Discovery **")
        lines = result.split("\n")
        assert lines[0] == "** Discovery **"

    def test_no_header_by_default(self) -> None:
        result = self.formatter.format(SAMPLE_DATA)
        assert result.startswith("\U0001f30c")
