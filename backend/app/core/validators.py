from urllib.parse import urlparse

ALLOWED_MEETING_DOMAINS: frozenset[str] = frozenset(
    {
        "zoom.us",
        "meet.google.com",
        "teams.microsoft.com",
        "whereby.com",
    }
)


class MeetingURLValidationError(ValueError):
    pass


def validate_meeting_url(url: str) -> str:
    if not url or not url.strip():
        raise MeetingURLValidationError("Meeting URL cannot be empty")

    url = url.strip()

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise MeetingURLValidationError(f"Invalid URL format: {e}") from e

    if parsed.scheme.lower() != "https":
        raise MeetingURLValidationError(
            f"Meeting URL must use HTTPS, got '{parsed.scheme}'"
        )

    hostname = parsed.hostname
    if not hostname:
        raise MeetingURLValidationError("Meeting URL must have a valid hostname")

    hostname = hostname.lower()

    if not _is_allowed_domain(hostname):
        raise MeetingURLValidationError(
            f"Meeting URL domain '{hostname}' is not allowed. "
            f"Allowed: {', '.join(sorted(ALLOWED_MEETING_DOMAINS))}"
        )

    return url


def _is_allowed_domain(hostname: str) -> bool:
    for allowed in ALLOWED_MEETING_DOMAINS:
        if hostname == allowed:
            return True
        if hostname.endswith(f".{allowed}"):
            return True
    return False
