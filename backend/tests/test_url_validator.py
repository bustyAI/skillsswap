import pytest

from app.core.validators import (
    ALLOWED_MEETING_DOMAINS,
    MeetingURLValidationError,
    validate_meeting_url,
)


class TestValidateMeetingURL:
    def test_valid_zoom_url(self) -> None:
        url = "https://zoom.us/j/1234567890"
        assert validate_meeting_url(url) == url

    def test_valid_zoom_subdomain(self) -> None:
        url = "https://us02web.zoom.us/j/1234567890"
        assert validate_meeting_url(url) == url

    def test_valid_google_meet_url(self) -> None:
        url = "https://meet.google.com/abc-defg-hij"
        assert validate_meeting_url(url) == url

    def test_valid_teams_url(self) -> None:
        url = "https://teams.microsoft.com/l/meetup-join/abc123"
        assert validate_meeting_url(url) == url

    def test_valid_whereby_url(self) -> None:
        url = "https://whereby.com/my-room"
        assert validate_meeting_url(url) == url

    def test_valid_whereby_subdomain(self) -> None:
        url = "https://mycompany.whereby.com/meeting"
        assert validate_meeting_url(url) == url

    def test_strips_whitespace(self) -> None:
        url = "  https://zoom.us/j/123  "
        assert validate_meeting_url(url) == url.strip()

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(MeetingURLValidationError, match="cannot be empty"):
            validate_meeting_url("")

    def test_rejects_whitespace_only(self) -> None:
        with pytest.raises(MeetingURLValidationError, match="cannot be empty"):
            validate_meeting_url("   ")

    def test_rejects_http_scheme(self) -> None:
        with pytest.raises(MeetingURLValidationError, match="must use HTTPS"):
            validate_meeting_url("http://zoom.us/j/123")

    def test_rejects_no_scheme(self) -> None:
        with pytest.raises(MeetingURLValidationError, match="must use HTTPS"):
            validate_meeting_url("zoom.us/j/123")

    def test_rejects_disallowed_domain(self) -> None:
        with pytest.raises(MeetingURLValidationError, match="not allowed"):
            validate_meeting_url("https://evil.com/meeting")

    def test_rejects_lookalike_domain(self) -> None:
        with pytest.raises(MeetingURLValidationError, match="not allowed"):
            validate_meeting_url("https://fakerzoom.us/j/123")

    def test_rejects_suffix_attack(self) -> None:
        with pytest.raises(MeetingURLValidationError, match="not allowed"):
            validate_meeting_url("https://notzoom.us/j/123")

    def test_case_insensitive_hostname(self) -> None:
        url = "https://ZOOM.US/j/123"
        assert validate_meeting_url(url) == url

    def test_case_insensitive_scheme(self) -> None:
        url = "https://zoom.us/j/123"
        result = validate_meeting_url(url)
        assert result == url


class TestAllowedDomains:
    def test_all_domains_present(self) -> None:
        expected = {"zoom.us", "meet.google.com", "teams.microsoft.com", "whereby.com"}
        assert expected == ALLOWED_MEETING_DOMAINS
