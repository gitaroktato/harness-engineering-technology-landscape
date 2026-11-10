"""Favicon download and caching for landscape items."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import requests

from .models import LandscapeItem

logger = logging.getLogger(__name__)


def _normalize_domain(url: str) -> str:
    """Normalize a domain to a safe filename component."""
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]
    # Replace unsafe characters
    domain = domain.replace(".", "_").replace(":", "_").replace("/", "_")
    return domain


_IMAGE_CONTENT_TYPE_MAP: dict[str, str] = {
    "image/x-icon": ".ico",
    "image/vnd.microsoft.icon": ".ico",
    "image/png": ".png",
    "image/svg+xml": ".svg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/jpeg": ".jpg",
}

_KNOWN_IMAGE_EXTENSIONS = frozenset({".ico", ".png", ".svg", ".gif", ".webp", ".jpg", ".jpeg"})


def _extension_for_favicon(url: str, content_type: str = "") -> str:
    """Return the file extension for a favicon URL.

    Priority:
    1. Extension from the URL path if it is a recognised image extension.
    2. Extension derived from the Content-Type header.
    3. Default: ``.ico``.

    Args:
        url: The favicon URL.
        content_type: The value of the Content-Type response header (may be empty).

    Returns:
        A file extension string including the leading dot, e.g. ``".svg"``.
    """
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in _KNOWN_IMAGE_EXTENSIONS:
        return suffix
    if content_type:
        mime = content_type.split(";")[0].strip()
        if mime in _IMAGE_CONTENT_TYPE_MAP:
            return _IMAGE_CONTENT_TYPE_MAP[mime]
    return ".ico"


def _resolve_favicon_url(item_name: str, item_url: str | None) -> str:
    """Determine the favicon URL for an item.

    Tries multiple favicon locations to find one that exists:
    1. /favicon.ico, /favicon.png, /favicon.svg at the URL
    2. /favicon.ico at the domain root
    3. The domain root URL itself (many sites serve favicon there)
    4. GitHub default as last resort

    Args:
        item_name: Display name (for logging).
        item_url: The item's URL.

    Returns:
        The best favicon URL found, or GitHub default.
    """
    if not item_url:
        return "https://github.com/favicon.ico"

    base_url = item_url.rstrip("/")

    # Try explicit favicon paths at the URL
    for path in ["/favicon.ico", "/favicon.png", "/favicon.svg", "/assets/favicon.ico"]:
        test_url = base_url + path
        try:
            resp = requests.head(test_url, timeout=5, allow_redirects=True)
            if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
                return test_url
        except requests.RequestException:
            continue

    # Try /favicon.ico at the domain root
    parsed = urlparse(base_url)
    domain_root = f"{parsed.scheme}://{parsed.netloc}"
    domain_favicon = f"{domain_root}/favicon.ico"
    try:
        resp = requests.head(domain_favicon, timeout=5, allow_redirects=True)
        if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
            return domain_favicon
    except requests.RequestException:
        pass

    # Try the domain root URL itself (many sites serve favicon there)
    try:
        resp = requests.head(domain_root, timeout=5, allow_redirects=True)
        if resp.status_code == 200:
            return domain_root
    except requests.RequestException:
        pass

    # Last resort: GitHub default
    return "https://github.com/favicon.ico"


def download_favicons(
    items: Iterable[LandscapeItem],
    output_dir: Path,
) -> dict[str, str]:
    """Download favicons for landscape items.

    For each item that has either an explicit ``favicon`` URL or a ``url``,
    downloads the favicon to the output directory.  The explicit ``favicon``
    field takes priority over automatic URL-based discovery via
    :func:`_resolve_favicon_url`.

    Deduplication key:
    - Items with an explicit ``favicon`` URL → deduplicated by that URL.
    - Items without ``favicon`` → deduplicated by their ``url``.

    Items that have neither ``favicon`` nor ``url`` are skipped.

    Args:
        items: Iterable of LandscapeItem instances.
        output_dir: Directory to save downloaded favicons.

    Returns:
        Mapping of item_name -> local file path (empty string on failure).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded: dict[str, str] = {}

    # Deduplicate: key = explicit favicon URL if set, otherwise the website URL.
    seen: dict[str, LandscapeItem] = {}
    for item in items:
        key = item.favicon or (item.url.rstrip("/") if item.url else None)
        if key and key not in seen:
            seen[key] = item

    for key, item in seen.items():
        # Honor the explicit favicon override; fall back to HTTP-probe discovery.
        if item.favicon:
            favicon_url = item.favicon
        else:
            favicon_url = _resolve_favicon_url(item.name, item.url)

        # Derive a safe filename from whichever URL we know about.
        domain = _normalize_domain(item.url) if item.url else _normalize_domain(key)

        # Cache check: honour any previously downloaded extension for this domain.
        cached = next(output_dir.glob(f"{domain}.*"), None)
        if cached is not None:
            downloaded[item.name] = str(cached)
            continue

        try:
            logger.info("Downloading favicon for %s -> %s", item.name, favicon_url)
            resp = requests.get(favicon_url, timeout=10, stream=True)
            resp.raise_for_status()

            # Only save if we actually got an image.
            # The .ico extension fallback only fires when the server sends no
            # Content-Type header at all; an explicit non-image type wins.
            content_type = resp.headers.get("Content-Type", "")
            is_image = "image" in content_type or (
                not content_type and favicon_url.endswith(".ico")
            )
            if is_image:
                ext = _extension_for_favicon(favicon_url, content_type)
                local_path = output_dir / f"{domain}{ext}"
                local_path.write_bytes(resp.content)
                downloaded[item.name] = str(local_path)
                logger.info("Saved favicon: %s", local_path)
            else:
                logger.warning(
                    "Skipping non-image response for %s (Content-Type: %s)",
                    item.name,
                    content_type,
                )
                downloaded[item.name] = ""

        except requests.RequestException as e:
            logger.warning("Failed to download favicon for %s: %s", item.name, e)
            downloaded[item.name] = ""  # Signal failure

    return downloaded
