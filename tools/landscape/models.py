"""Data models for the landscape configuration."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from dataclasses import dataclass, field


@dataclass
class LandscapeItem:
    """A single technology item in the landscape."""

    name: str
    repo: str | None = None  # "owner/repo" format for GitHub lookup
    url: str | None = None
    description: str | None = None
    icon: str | None = None  # optional icon filename from assets/icons/
    favicon: str | None = None  # optional direct favicon URL (overrides convention)
    optional: bool = False  # if True, skip generation on validation failure

    @property
    def github_key(self) -> str | None:
        """Return the GitHub lookup key if this is a GitHub repo."""
        if self.repo and "/" in self.repo:
            return self.repo
        return None

    @property
    def is_github(self) -> bool:
        """Check if this item is a GitHub repository."""
        return self.github_key is not None

    @property
    def display_name(self) -> str:
        """Return the display name, falling back to repo name."""
        return self.name

    @property
    def repo_short(self) -> str:
        """Return the repo slug, or the hostname if no repo is set.

        Examples:
            - repo "owner/repo"          → "owner/repo"
            - url "https://docs.fabro.sh/..." → "docs.fabro.sh"
            - no repo and no url         → "N/A"
        """
        if self.repo:
            return self.repo
        if self.url:
            return urlparse(self.url).netloc
        return "N/A"

    @property
    def favicon_url(self) -> str:
        """Return the favicon URL for this item.

        Priority:
        1. Explicit ``favicon`` URL (non-conventional override)
        2. Local ``icon`` file from assets/icons/
        3. GitHub default for GitHub repos
        4. Domain-based favicon for items with a URL
        5. GitHub default fallback
        """
        if self.favicon:
            return self.favicon
        if self.icon:
            local = Path("assets/icons") / self.icon
            if local.exists():
                return f"assets/icons/{self.icon}"
            # Local file missing - fall through to external URL
        if self.is_github:
            return "https://github.com/favicon.ico"
        if self.url:
            domain = self.url.replace("https://", "").replace("http://", "")
            return f"https://{domain}/favicon.ico"
        return "https://github.com/favicon.ico"


@dataclass
class LandscapeSubGroup:
    """A named column group within a category swimlane.

    Sub-groups are rendered as nested swimlane containers inside their
    parent category, providing visual column headers (e.g. "Skill Reference",
    "Skill Security Scanners") that group related items together.
    """

    name: str
    items: list[LandscapeItem] = field(default_factory=list)


@dataclass
class LandscapeCategory:
    """A category section in the landscape."""

    name: str
    items: list[LandscapeItem] = field(default_factory=list)
    groups: list[LandscapeSubGroup] = field(default_factory=list)
    subtitle: str | None = None

    @property
    def has_groups(self) -> bool:
        """True when this category uses named column sub-groups."""
        return bool(self.groups)

    @property
    def all_items(self) -> list[LandscapeItem]:
        """All items: direct ``items`` plus every item inside ``groups``."""
        result: list[LandscapeItem] = list(self.items)
        for group in self.groups:
            result.extend(group.items)
        return result

    def add_item(self, item: LandscapeItem) -> None:
        """Add a direct (ungrouped) item to this category."""
        self.items.append(item)

    def add_group(self, group: LandscapeSubGroup) -> None:
        """Add a sub-group to this category."""
        self.groups.append(group)


@dataclass
class LandscapeConfig:
    """Top-level landscape configuration."""

    title: str
    categories: list[LandscapeCategory] = field(default_factory=list)

    def category_count(self) -> int:
        """Return the number of categories."""
        return len(self.categories)

    def item_count(self) -> int:
        """Return the total number of items across all categories and groups."""
        return sum(len(cat.all_items) for cat in self.categories)

    def all_items(self) -> list[LandscapeItem]:
        """Return all items across every category and sub-group."""
        return [item for cat in self.categories for item in cat.all_items]

    def github_items(self) -> list[tuple[LandscapeCategory, LandscapeItem]]:
        """Return all items (including sub-group items) that need GitHub lookup."""
        result: list[tuple[LandscapeCategory, LandscapeItem]] = []
        for cat in self.categories:
            for item in cat.all_items:
                if item.is_github:
                    result.append((cat, item))
        return result
