"""GitHub API client with retries and rate limit handling."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger(__name__)


@dataclass
class GitHubRepoInfo:
    """Represents a GitHub repository's metadata."""

    stars: int
    description: str
    url: str
    owner: str
    name: str
    is_private: bool = False
    exists: bool = True


class GitHubClient:
    """Client for GitHub API with retry logic and caching support."""

    BASE_URL = "https://api.github.com/repos/{owner}/{repo}"
    MAX_RETRIES = 5
    BASE_DELAY = 1.0  # seconds

    def __init__(self, cache: Any = None, dry_run: bool = False) -> None:
        self.cache = cache
        self.dry_run = dry_run
        self._session = requests.Session()
        self._session.headers.update(
            {"Accept": "application/vnd.github.v3+json"}
        )
        # Check if we have a token for higher rate limits
        import os
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            self._session.headers.update(
                {"Authorization": f"Bearer {token}"}
            )

    def get_repo_info(
        self,
        owner: str,
        repo: str,
        favicon_url: str | None = None,
    ) -> GitHubRepoInfo | None:
        """Fetch repository info from GitHub API with retries.

        Args:
            owner: GitHub repository owner.
            repo: GitHub repository name.
            favicon_url: Explicit favicon URL to store in the cache.  When
                provided this value takes precedence over the generic GitHub
                fallback (``https://github.com/favicon.ico``).
        """
        cache_key = f"{owner}/{repo}"

        # Check cache first
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached and cached.stars is not None:
                logger.debug("Cache hit: %s", cache_key)
                return GitHubRepoInfo(
                    stars=cached.stars,
                    description=cached.description or "",
                    url=f"https://github.com/{cache_key}",
                    owner=owner,
                    name=repo,
                )

        if self.dry_run:
            logger.warning("Dry run: skipping GitHub lookup for %s", cache_key)
            return None

        last_error: Exception | None = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self._session.get(
                    self.BASE_URL.format(owner=owner, repo=repo),
                    timeout=15,
                )

                # Handle rate limiting
                if response.status_code == 403:
                    remaining = int(
                        response.headers.get("X-RateLimit-Remaining", 0)
                    )
                    if remaining == 0:
                        reset_time = int(
                            response.headers.get("X-RateLimit-Reset", 0)
                        )
                        wait = max(reset_time - time.time(), 1)
                        logger.warning(
                            "Rate limited. Waiting %.0fs until reset", wait
                        )
                        time.sleep(wait)
                        continue

                if response.status_code == 404:
                    logger.warning("Repo not found: %s", cache_key)
                    return GitHubRepoInfo(
                        stars=0,
                        description="",
                        url=f"https://github.com/{cache_key}",
                        owner=owner,
                        name=repo,
                        exists=False,
                    )

                response.raise_for_status()
                data: dict[str, Any] = response.json()

                info = GitHubRepoInfo(
                    stars=data.get("stargazers_count", 0),
                    description=data.get("description") or "",
                    url=data.get("html_url", ""),
                    owner=owner,
                    name=repo,
                    is_private=data.get("private", False),
                )

                # Cache the result
                if self.cache:
                    from .cache import CachedItem

                    self.cache.put(
                        CachedItem(
                            key=cache_key,
                            stars=info.stars,
                            description=info.description,
                            favicon_url=favicon_url or "https://github.com/favicon.ico",
                            favicon_path=None,
                            fetched_at=time.time(),
                            source="github",
                        )
                    )

                return info

            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(
                    "Timeout for %s (attempt %d/%d)",
                    cache_key,
                    attempt + 1,
                    self.MAX_RETRIES,
                )
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(
                    "Request error for %s (attempt %d/%d): %s",
                    cache_key,
                    attempt + 1,
                    self.MAX_RETRIES,
                    e,
                )

            # Exponential backoff with jitter
            delay = self.BASE_DELAY * (2**attempt)
            jitter = delay * 0.1 * (attempt % 3)
            time.sleep(delay + jitter)

        logger.error(
            "Failed to fetch %s after %d attempts: %s",
            cache_key,
            self.MAX_RETRIES,
            last_error,
        )
        return None
