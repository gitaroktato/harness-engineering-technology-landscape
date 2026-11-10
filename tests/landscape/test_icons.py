"""Tests for the favicon download logic in icons.py.

Covers the three acceptance criteria from the plan:
  AC1 - Items with an explicit `favicon` URL always have that URL downloaded,
        regardless of whether they also have a `url` field.
  AC2 - Items with only a `favicon` and no `url` are no longer silently skipped.
  AC3 - Items with a `url` but no `favicon` continue to use
        `_resolve_favicon_url` as before (no regression).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.landscape.icons import download_favicons
from tools.landscape.models import LandscapeItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_image_response(url: str) -> MagicMock:
    """Return a mock HTTP response that looks like an image."""
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "image/x-icon"}
    resp.content = b"\x00" * 16  # minimal fake icon bytes
    resp.raise_for_status = MagicMock()
    return resp


def _fake_non_image_response(url: str) -> MagicMock:
    """Return a mock HTTP response that does NOT look like an image."""
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "text/html"}
    resp.content = b"<html/>"
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# AC2 — item with favicon but NO url is no longer silently skipped
# ---------------------------------------------------------------------------

class TestFaviconOnlyItem:
    """Items that have a favicon URL but no website URL must be processed."""

    def test_item_with_favicon_no_url_is_downloaded(self, tmp_path: Path) -> None:
        """AC2: favicon-only item must produce a downloaded entry, not be skipped."""
        item = LandscapeItem(
            name="FaviconOnly",
            favicon="https://cdn.example.com/favicon.ico",
        )

        with patch("tools.landscape.icons.requests.get", return_value=_fake_image_response("")) as mock_get:
            result = download_favicons([item], tmp_path)

        assert "FaviconOnly" in result, (
            "Item with only a favicon URL must appear in the result dict"
        )
        assert result["FaviconOnly"] != "", (
            "favicon-only item must have a non-empty local path on success"
        )
        # The explicit favicon URL must be fetched directly — _resolve_favicon_url
        # must NOT be called (it would make HTTP HEAD requests for url-based guessing)
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert call_url == "https://cdn.example.com/favicon.ico", (
            "The explicit favicon URL must be passed to requests.get, not a guessed one"
        )

    def test_item_with_favicon_no_url_written_to_disk(self, tmp_path: Path) -> None:
        """AC2: favicon-only item's icon bytes are written to the output directory."""
        item = LandscapeItem(
            name="WriteCheck",
            favicon="https://cdn.example.com/icon.ico",
        )

        with patch("tools.landscape.icons.requests.get", return_value=_fake_image_response("")):
            result = download_favicons([item], tmp_path)

        local_path = result.get("WriteCheck", "")
        assert local_path, "Expected a file path in result"
        assert Path(local_path).exists(), "Icon file must exist on disk"
        assert Path(local_path).read_bytes() == b"\x00" * 16


# ---------------------------------------------------------------------------
# AC1 — item with explicit favicon AND a url uses the explicit favicon URL
# ---------------------------------------------------------------------------

class TestExplicitFaviconOverridesUrl:
    """The favicon field must override automatic URL-based discovery."""

    def test_explicit_favicon_used_over_url_resolution(self, tmp_path: Path) -> None:
        """AC1: When favicon is set, _resolve_favicon_url must NOT be called."""
        item = LandscapeItem(
            name="ExplicitFavicon",
            url="https://example.com",
            favicon="https://brand.example.com/logo.ico",
        )

        with (
            patch("tools.landscape.icons.requests.get", return_value=_fake_image_response("")) as mock_get,
            patch("tools.landscape.icons._resolve_favicon_url") as mock_resolve,
        ):
            result = download_favicons([item], tmp_path)

        mock_resolve.assert_not_called(), (
            "_resolve_favicon_url must not be called when favicon is explicitly set"
        )
        assert result.get("ExplicitFavicon") != "", "Download must succeed"
        call_url = mock_get.call_args[0][0]
        assert call_url == "https://brand.example.com/logo.ico", (
            "The explicit favicon URL must be fetched, not a guessed one"
        )

    def test_explicit_favicon_file_written_when_url_also_present(self, tmp_path: Path) -> None:
        """AC1: Icon file is written when both favicon and url are set."""
        item = LandscapeItem(
            name="BothFaviconAndUrl",
            url="https://example.com",
            favicon="https://brand.example.com/logo.ico",
        )

        with patch("tools.landscape.icons.requests.get", return_value=_fake_image_response("")):
            result = download_favicons([item], tmp_path)

        local_path = result.get("BothFaviconAndUrl", "")
        assert local_path, "Expected a non-empty path in result"
        assert Path(local_path).exists(), "Icon file must exist on disk"


# ---------------------------------------------------------------------------
# AC3 — item with url but no favicon continues to use _resolve_favicon_url
# ---------------------------------------------------------------------------

class TestUrlOnlyItemUsesResolve:
    """Items without an explicit favicon must still use _resolve_favicon_url."""

    def test_url_only_item_calls_resolve_favicon_url(self, tmp_path: Path) -> None:
        """AC3: _resolve_favicon_url is invoked for items without favicon."""
        item = LandscapeItem(
            name="UrlOnly",
            url="https://example.com",
        )
        guessed_url = "https://example.com/favicon.ico"

        with (
            patch(
                "tools.landscape.icons._resolve_favicon_url",
                return_value=guessed_url,
            ) as mock_resolve,
            patch("tools.landscape.icons.requests.get", return_value=_fake_image_response("")) as mock_get,
        ):
            result = download_favicons([item], tmp_path)

        mock_resolve.assert_called_once(), (
            "_resolve_favicon_url must be called for url-only items"
        )
        assert result.get("UrlOnly") != "", "Download must succeed for url-only item"
        call_url = mock_get.call_args[0][0]
        assert call_url == guessed_url, "The resolved URL must be fetched"

    def test_url_only_item_file_written(self, tmp_path: Path) -> None:
        """AC3: Icon is written to disk for url-only items (regression guard)."""
        item = LandscapeItem(
            name="UrlOnlyWrite",
            url="https://example.com",
        )

        with (
            patch(
                "tools.landscape.icons._resolve_favicon_url",
                return_value="https://example.com/favicon.ico",
            ),
            patch("tools.landscape.icons.requests.get", return_value=_fake_image_response("")),
        ):
            result = download_favicons([item], tmp_path)

        local_path = result.get("UrlOnlyWrite", "")
        assert local_path, "Expected a non-empty path"
        assert Path(local_path).exists(), "Icon file must exist on disk"


# ---------------------------------------------------------------------------
# Deduplication behaviour
# ---------------------------------------------------------------------------

class TestDeduplication:
    """Deduplication must use the correct key for each item type."""

    def test_two_items_same_url_downloaded_once(self, tmp_path: Path) -> None:
        """Two items sharing the same url produce one download."""
        items = [
            LandscapeItem(name="ItemA", url="https://shared.com"),
            LandscapeItem(name="ItemB", url="https://shared.com"),
        ]

        with (
            patch(
                "tools.landscape.icons._resolve_favicon_url",
                return_value="https://shared.com/favicon.ico",
            ),
            patch("tools.landscape.icons.requests.get", return_value=_fake_image_response("")) as mock_get,
        ):
            download_favicons(items, tmp_path)

        assert mock_get.call_count == 1, (
            "Only one HTTP GET should be made for two items sharing the same URL"
        )

    def test_two_items_same_favicon_url_downloaded_once(self, tmp_path: Path) -> None:
        """Two items sharing the same explicit favicon URL produce one download."""
        items = [
            LandscapeItem(name="ItemA", favicon="https://cdn.example.com/icon.ico"),
            LandscapeItem(name="ItemB", favicon="https://cdn.example.com/icon.ico"),
        ]

        with patch("tools.landscape.icons.requests.get", return_value=_fake_image_response("")) as mock_get:
            download_favicons(items, tmp_path)

        assert mock_get.call_count == 1, (
            "Only one HTTP GET for two items sharing the same explicit favicon URL"
        )

    def test_already_downloaded_favicon_not_re_fetched(self, tmp_path: Path) -> None:
        """If the icon file already exists, requests.get must not be called."""
        item = LandscapeItem(
            name="Cached",
            favicon="https://cdn.example.com/cached.ico",
        )
        # Pre-create the icon file so it looks already downloaded
        # We need to know the expected filename first; use the normaliser logic
        from tools.landscape.icons import _normalize_domain
        domain = _normalize_domain("https://cdn.example.com/cached.ico")
        (tmp_path / f"{domain}.ico").write_bytes(b"\xff" * 4)

        with patch("tools.landscape.icons.requests.get") as mock_get:
            result = download_favicons([item], tmp_path)

        mock_get.assert_not_called(), "No HTTP request should be made when file is cached"
        assert result.get("Cached") != "", "Cached item must still appear in results"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Failures during download must be recorded as empty strings, not exceptions."""

    def test_network_failure_returns_empty_string(self, tmp_path: Path) -> None:
        """A requests.RequestException must not propagate; result entry is ''."""
        import requests as _requests

        item = LandscapeItem(
            name="NetFail",
            favicon="https://cdn.example.com/fail.ico",
        )

        with patch(
            "tools.landscape.icons.requests.get",
            side_effect=_requests.RequestException("timeout"),
        ):
            result = download_favicons([item], tmp_path)

        assert "NetFail" in result
        assert result["NetFail"] == "", "Failed download must produce empty string path"

    def test_non_image_response_returns_empty_string(self, tmp_path: Path) -> None:
        """A non-image Content-Type must not be saved; result entry is ''."""
        item = LandscapeItem(
            name="NotAnImage",
            favicon="https://cdn.example.com/notimage.ico",
        )

        with patch(
            "tools.landscape.icons.requests.get",
            return_value=_fake_non_image_response(""),
        ):
            result = download_favicons([item], tmp_path)

        assert "NotAnImage" in result
        assert result["NotAnImage"] == "", (
            "Non-image response must produce empty string path"
        )


# ---------------------------------------------------------------------------
# Extension derivation — saved file extension must match the favicon source
# ---------------------------------------------------------------------------

class TestExtensionDerivation:
    """The saved file extension must match the favicon source."""

    def test_svg_favicon_url_saves_as_svg(self, tmp_path: Path) -> None:
        """A favicon URL ending in .svg must produce a .svg file on disk."""
        item = LandscapeItem(
            name="SvgFavicon",
            favicon="https://example.com/icon.svg",
        )
        with patch("tools.landscape.icons.requests.get", return_value=_fake_image_response("")):
            result = download_favicons([item], tmp_path)

        local_path = Path(result["SvgFavicon"])
        assert local_path.suffix == ".svg", f"Expected .svg, got {local_path.suffix}"
        assert local_path.exists()

    def test_content_type_fallback_extension(self, tmp_path: Path) -> None:
        """When URL has no recognisable extension, Content-Type determines the suffix."""
        item = LandscapeItem(
            name="NoExtIcon",
            favicon="https://example.com/icon",
        )
        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {"Content-Type": "image/svg+xml"}
        resp.content = b"<svg/>"
        resp.raise_for_status = MagicMock()

        with patch("tools.landscape.icons.requests.get", return_value=resp):
            result = download_favicons([item], tmp_path)

        local_path = Path(result["NoExtIcon"])
        assert local_path.suffix == ".svg", f"Expected .svg from Content-Type, got {local_path.suffix}"
        assert local_path.exists()
