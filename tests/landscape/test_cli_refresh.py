"""Tests for the `refresh` CLI command.

The "bug" tests below assert the *correct* (post-fix) behaviour and therefore
currently FAIL because the bug is still present: running `refresh` empties the
cache file instead of repopulating it with fresh data from GitHub.  They will
start passing once the fix is implemented.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from tools.landscape.cache import Cache, CachedItem
from tools.landscape.cli import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GITHUB_YAML = """\
title: Test Landscape
categories:
  - name: SDD
    color: "#dae8fc"
    stroke: "#6c8ebf"
    items:
      - name: OpenSpec
        repo: Fission-AI/OpenSpec
      - name: AnotherTool
        repo: some-org/another-tool
"""


def _make_cache_with_entries(cache_file: Path) -> Cache:
    """Return a Cache pre-populated with two GitHub entries."""
    cache = Cache(cache_file)
    cache.put(
        CachedItem(
            key="Fission-AI/OpenSpec",
            stars=42,
            description="An openspec tool",
            favicon_url=None,
            favicon_path=None,
            fetched_at=time.time(),
            source="github",
        )
    )
    cache.put(
        CachedItem(
            key="some-org/another-tool",
            stars=7,
            description="Another tool",
            favicon_url=None,
            favicon_path=None,
            fetched_at=time.time(),
            source="github",
        )
    )
    return cache


def _mock_github_response(owner: str, repo: str) -> MagicMock:
    """Return a fake successful requests.Response for a GitHub repo API call."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "stargazers_count": 1,
        "description": f"Stub for {owner}/{repo}",
        "html_url": f"https://github.com/{owner}/{repo}",
        "private": False,
    }
    response.raise_for_status.return_value = None
    return response


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRefreshAll:
    """Tests for `refresh --all`."""

    def test_all_flag_clears_the_cache_file(self, tmp_path: Path) -> None:
        """--all should wipe the cache file entirely."""
        cache_file = tmp_path / "cache.json"
        _make_cache_with_entries(cache_file)
        assert json.loads(cache_file.read_text())  # sanity: file has data

        with patch("tools.landscape.cli.CACHE_PATH", cache_file):
            result = CliRunner().invoke(main, ["refresh", "--all"])

        assert result.exit_code == 0
        assert "Cache cleared." in result.output
        assert json.loads(cache_file.read_text()) == {}

    def test_all_flag_prints_confirmation(self, tmp_path: Path) -> None:
        """--all should print 'Cache cleared.' and nothing else."""
        cache_file = tmp_path / "cache.json"

        with patch("tools.landscape.cli.CACHE_PATH", cache_file):
            result = CliRunner().invoke(main, ["refresh", "--all"])

        assert result.exit_code == 0
        assert result.output.strip() == "Cache cleared."


class TestRefreshNoConfig:
    """Tests for `refresh` when no config file exists."""

    def test_missing_config_leaves_cache_untouched(self, tmp_path: Path) -> None:
        """When CONFIG_PATH does not exist the cache must not be modified."""
        cache_file = tmp_path / "cache.json"
        _make_cache_with_entries(cache_file)
        original = json.loads(cache_file.read_text())

        missing_config = tmp_path / "nonexistent.yaml"

        with (
            patch("tools.landscape.cli.CACHE_PATH", cache_file),
            patch("tools.landscape.cli.CONFIG_PATH", missing_config),
        ):
            result = CliRunner().invoke(main, ["refresh"])

        assert result.exit_code == 0
        assert "No config found" in result.output
        assert json.loads(cache_file.read_text()) == original


class TestRefreshWithConfig:
    """Tests for `refresh` when a config file is present."""

    def test_refresh_exits_successfully(self, tmp_path: Path) -> None:
        """refresh should exit with code 0."""
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(_GITHUB_YAML, encoding="utf-8")
        cache_file = tmp_path / "cache.json"

        with (
            patch("tools.landscape.cli.CACHE_PATH", cache_file),
            patch("tools.landscape.cli.CONFIG_PATH", config_file),
        ):
            result = CliRunner().invoke(main, ["refresh"])

        assert result.exit_code == 0

    def test_refresh_reports_each_github_key(self, tmp_path: Path) -> None:
        """refresh should print a 'Refreshed: <key>' line for every GitHub item."""
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(_GITHUB_YAML, encoding="utf-8")
        cache_file = tmp_path / "cache.json"

        with (
            patch("tools.landscape.cli.CACHE_PATH", cache_file),
            patch("tools.landscape.cli.CONFIG_PATH", config_file),
        ):
            result = CliRunner().invoke(main, ["refresh"])

        assert "Refreshed: Fission-AI/OpenSpec" in result.output
        assert "Refreshed: some-org/another-tool" in result.output

    def test_refresh_reports_removed_expired_count(self, tmp_path: Path) -> None:
        """refresh should print 'Removed N expired entries.' at the end."""
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(_GITHUB_YAML, encoding="utf-8")
        cache_file = tmp_path / "cache.json"

        with (
            patch("tools.landscape.cli.CACHE_PATH", cache_file),
            patch("tools.landscape.cli.CONFIG_PATH", config_file),
        ):
            result = CliRunner().invoke(main, ["refresh"])

        assert "Removed" in result.output
        assert "expired entries" in result.output

    def test_bug_refresh_repopulates_cache_file(self, tmp_path: Path) -> None:
        """After `refresh`, the on-disk cache must contain a fresh entry for
        every GitHub item listed in the config.

        requests.Session.get is mocked so the test does not make real network
        calls while still exercising the full GitHubClient + Cache.put() path.
        """
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(_GITHUB_YAML, encoding="utf-8")
        cache_file = tmp_path / "cache.json"
        _make_cache_with_entries(cache_file)

        with (
            patch("tools.landscape.cli.CACHE_PATH", cache_file),
            patch("tools.landscape.cli.CONFIG_PATH", config_file),
            patch(
                "requests.Session.get",
                side_effect=lambda url, **kw: _mock_github_response(
                    *url.rstrip("/").split("/")[-2:]
                ),
            ),
        ):
            CliRunner().invoke(main, ["refresh"])

        on_disk = json.loads(cache_file.read_text())
        assert on_disk != {}, "Cache is empty after refresh — the bug is still present."
        assert "Fission-AI/OpenSpec" in on_disk
        assert "some-org/another-tool" in on_disk

    def test_bug_refresh_restores_keys_in_cache(self, tmp_path: Path) -> None:
        """After `refresh`, Cache.get() must return a fresh entry for every
        GitHub key that was in the config.

        requests.Session.get is mocked so the test does not make real network
        calls while still exercising the full GitHubClient + Cache.put() path.
        """
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(_GITHUB_YAML, encoding="utf-8")
        cache_file = tmp_path / "cache.json"
        _make_cache_with_entries(cache_file)

        with (
            patch("tools.landscape.cli.CACHE_PATH", cache_file),
            patch("tools.landscape.cli.CONFIG_PATH", config_file),
            patch(
                "requests.Session.get",
                side_effect=lambda url, **kw: _mock_github_response(
                    *url.rstrip("/").split("/")[-2:]
                ),
            ),
        ):
            CliRunner().invoke(main, ["refresh"])

        reloaded = Cache(cache_file)
        assert reloaded.get("Fission-AI/OpenSpec") is not None, (
            "Key 'Fission-AI/OpenSpec' is missing — the bug is still present."
        )
        assert reloaded.get("some-org/another-tool") is not None, (
            "Key 'some-org/another-tool' is missing — the bug is still present."
        )

    def test_bug_refresh_creates_github_client(self, tmp_path: Path) -> None:
        """refresh must instantiate GitHubClient to re-fetch data from GitHub.

        Currently FAILS because no GitHubClient is ever created inside the
        refresh command, so no network calls are made and the cache stays empty.
        """
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(_GITHUB_YAML, encoding="utf-8")
        cache_file = tmp_path / "cache.json"

        with (
            patch("tools.landscape.cli.CACHE_PATH", cache_file),
            patch("tools.landscape.cli.CONFIG_PATH", config_file),
            patch("tools.landscape.cli.GitHubClient") as mock_gh_class,
        ):
            CliRunner().invoke(main, ["refresh"])

        mock_gh_class.assert_called_once()

    def test_explicit_favicon_in_yaml_is_stored_in_cache(
        self, tmp_path: Path
    ) -> None:
        """When a GitHub item has an explicit ``favicon:`` URL in the YAML
        config, the cache must store that URL — not the generic GitHub fallback.

        This is a regression test for the bug where ``github.py`` always writes
        ``https://github.com/favicon.ico`` regardless of the item's ``favicon``
        field.
        """
        yaml_with_favicon = """\
title: Test Landscape
categories:
  - name: SDD
    color: "#dae8fc"
    stroke: "#6c8ebf"
    items:
      - name: OpenSpec
        repo: Fission-AI/OpenSpec
        favicon: https://openspec.dev/custom-icon.svg
"""
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(yaml_with_favicon, encoding="utf-8")
        cache_file = tmp_path / "cache.json"

        with (
            patch("tools.landscape.cli.CACHE_PATH", cache_file),
            patch("tools.landscape.cli.CONFIG_PATH", config_file),
            patch(
                "requests.Session.get",
                side_effect=lambda url, **kw: _mock_github_response(
                    *url.rstrip("/").split("/")[-2:]
                ),
            ),
        ):
            CliRunner().invoke(main, ["refresh"])

        reloaded = Cache(cache_file)
        entry = reloaded.get("Fission-AI/OpenSpec")
        assert entry is not None, "Entry missing from cache after refresh."
        assert entry.favicon_url == "https://openspec.dev/custom-icon.svg", (
            f"Expected explicit favicon URL from YAML, got: {entry.favicon_url!r}"
        )
