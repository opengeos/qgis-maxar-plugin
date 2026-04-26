"""Plugin-internal helpers for safe network access."""

from urllib.parse import urlparse


def require_https(url):
    """Reject any URL that does not use the https scheme.

    Args:
        url: URL to validate before passing to ``urlopen`` / ``urlretrieve``.

    Raises:
        ValueError: If the URL scheme is not ``https``.
    """
    if urlparse(url).scheme != "https":
        raise ValueError(f"URL must use https scheme: {url}")
