"""Tests for the landscape parser and models."""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import pytest
import yaml

from tools.landscape.cache import Cache, CachedItem
from tools.landscape.models import (
    LandscapeCategory,
    LandscapeConfig,
    LandscapeItem,
    LandscapeSubGroup,
)
from tools.landscape.parser import dump_landscape_yaml, parse_landscape_yaml


class TestLandscapeItem:
    """Tests for LandscapeItem model."""

    def test_github_key_from_owner_repo(self) -> None:
        """GitHub key should be extracted from owner/repo format."""
        item = LandscapeItem(name="test", repo="owner/repo")
        assert item.github_key == "owner/repo"

    def test_not_github_without_repo(self) -> None:
        """Item without repo is not a GitHub item."""
        item = LandscapeItem(name="test")
        assert item.github_key is None
        assert not item.is_github

    def test_not_github_bad_format(self) -> None:
        """Item with bad repo format is not a GitHub item."""
        item = LandscapeItem(name="test", repo="just-a-name")
        assert item.github_key is None
        assert not item.is_github

    def test_github_key_with_three_parts(self) -> None:
        """Three-part repo path returns the key (first two parts used in lookup)."""
        item = LandscapeItem(name="test", repo="owner/repo/sub")
        assert item.github_key == "owner/repo/sub"

    def test_display_name(self) -> None:
        """Display name returns the item name."""
        item = LandscapeItem(name="My Tool", repo="owner/repo")
        assert item.display_name == "My Tool"

    def test_repo_short(self) -> None:
        """Repo short returns the repo field."""
        item = LandscapeItem(name="My Tool", repo="owner/repo")
        assert item.repo_short == "owner/repo"

    def test_repo_short_none(self) -> None:
        """Repo short returns N/A when repo is None."""
        item = LandscapeItem(name="My Tool")
        assert item.repo_short == "N/A"

    def test_repo_short_url_only(self) -> None:
        """Repo short returns the hostname when only a URL is set."""
        item = LandscapeItem(name="My Tool", url="https://docs.fabro.sh/getting-started/introduction")
        assert item.repo_short == "docs.fabro.sh"

    def test_repo_short_url_only_simple(self) -> None:
        """Repo short returns the bare hostname for simple URLs."""
        item = LandscapeItem(name="My Tool", url="https://pi.dev/")
        assert item.repo_short == "pi.dev"

    def test_favicon_url_github(self) -> None:
        """GitHub items get GitHub favicon."""
        item = LandscapeItem(name="test", repo="owner/repo")
        assert item.favicon_url == "https://github.com/favicon.ico"

    def test_favicon_url_with_icon_local_missing(self) -> None:
        """Items with icon field fall back to external URL when local file missing."""
        item = LandscapeItem(name="test", repo="owner/repo", icon="my-icon.svg")
        # Local file doesn't exist, should fall back to GitHub favicon
        assert item.favicon_url == "https://github.com/favicon.ico"

    def test_favicon_url_with_url(self) -> None:
        """Non-GitHub items get domain-based external URL."""
        item = LandscapeItem(name="test", url="https://example.com")
        assert item.favicon_url == "https://example.com/favicon.ico"


class TestLandscapeConfig:
    """Tests for LandscapeConfig model."""

    def test_initial_values(self) -> None:
        """Default values are correct."""
        config = LandscapeConfig(title="Test")
        assert config.title == "Test"
        assert config.categories == []

    def test_category_count(self) -> None:
        """Category count reflects actual categories."""
        config = LandscapeConfig(title="Test")
        config.categories.append(LandscapeCategory(name="A"))
        config.categories.append(LandscapeCategory(name="B"))
        assert config.category_count() == 2

    def test_item_count(self) -> None:
        """Item count sums items across all categories."""
        config = LandscapeConfig(title="Test")
        cat_a = LandscapeCategory(name="A", items=[
            LandscapeItem(name="x"),
            LandscapeItem(name="y"),
        ])
        cat_b = LandscapeCategory(name="B", items=[
            LandscapeItem(name="z"),
        ])
        config.categories = [cat_a, cat_b]
        assert config.item_count() == 3

    def test_github_items(self) -> None:
        """Only GitHub items are returned by github_items()."""
        config = LandscapeConfig(title="Test")
        github_item = LandscapeItem(name="gh", repo="owner/repo")
        web_item = LandscapeItem(name="web", url="https://example.com")
        config.categories = [
            LandscapeCategory(name="C", items=[github_item, web_item]),
        ]
        result = config.github_items()
        assert len(result) == 1
        assert result[0][1].name == "gh"


class TestCache:
    """Tests for the cache layer."""

    def test_cache_creation(self, tmp_path: Path) -> None:
        """Cache creates the file on first access."""
        cache_file = tmp_path / "cache.json"
        cache = Cache(cache_file, ttl_seconds=3600)
        assert cache_file.exists()

    def test_put_and_get(self, tmp_path: Path) -> None:
        """Put and get operations work correctly."""
        cache_file = tmp_path / "cache.json"
        cache = Cache(cache_file)
        item = CachedItem(
            key="test",
            stars=100,
            description="A test",
            favicon_url="https://example.com/favicon.ico",
            favicon_path=None,
            fetched_at=time.time(),
            source="github",
        )
        cache.put(item)
        result = cache.get("test")
        assert result is not None
        assert result.stars == 100
        assert result.description == "A test"

    def test_cache_miss(self, tmp_path: Path) -> None:
        """Missing key returns None."""
        cache_file = tmp_path / "cache.json"
        cache = Cache(cache_file)
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self, tmp_path: Path) -> None:
        """Expired entries return None."""
        cache_file = tmp_path / "cache.json"
        cache = Cache(cache_file, ttl_seconds=0.001)  # nearly instant expiry
        item = CachedItem(
            key="test",
            stars=100,
            description="A test",
            favicon_url=None,
            favicon_path=None,
            fetched_at=0.0,  # long ago
            source="github",
        )
        cache.put(item)
        import time
        time.sleep(0.01)  # tiny delay
        assert cache.get("test") is None

    def test_refresh(self, tmp_path: Path) -> None:
        """Refresh removes a specific key."""
        cache_file = tmp_path / "cache.json"
        cache = Cache(cache_file)
        now = time.time()
        item1 = CachedItem(
            key="key1", stars=100, description="d",
            favicon_url=None, favicon_path=None,
            fetched_at=now, source="github",
        )
        item2 = CachedItem(
            key="key2", stars=200, description="d",
            favicon_url=None, favicon_path=None,
            fetched_at=now, source="github",
        )
        cache.put(item1)
        cache.put(item2)
        assert cache.get("key1") is not None
        assert cache.get("key2") is not None

        cache.refresh("key1")
        assert cache.get("key1") is None
        assert cache.get("key2") is not None

    def test_clear(self, tmp_path: Path) -> None:
        """Clear removes all entries."""
        cache_file = tmp_path / "cache.json"
        cache = Cache(cache_file)
        cache.put(CachedItem(
            key="k1", stars=1, description="d",
            favicon_url=None, favicon_path=None,
            fetched_at=time.time(), source="github",
        ))
        cache.clear()
        assert cache.get("k1") is None

    def test_remove_expired(self, tmp_path: Path) -> None:
        """remove_expired cleans up expired entries."""
        cache_file = tmp_path / "cache.json"
        cache = Cache(cache_file, ttl_seconds=0.001)  # nearly instant
        now = time.time()
        item1 = CachedItem(
            key="old", stars=1, description="d",
            favicon_url=None, favicon_path=None,
            fetched_at=0.0, source="github",
        )
        item2 = CachedItem(
            key="new", stars=2, description="d",
            favicon_url=None, favicon_path=None,
            fetched_at=now, source="github",
        )
        cache.put(item1)
        cache.put(item2)
        removed = cache.remove_expired()
        assert removed == 1

    def test_keys(self, tmp_path: Path) -> None:
        """keys() returns all cached keys."""
        cache_file = tmp_path / "cache.json"
        cache = Cache(cache_file)
        now = time.time()
        cache.put(CachedItem(
            key="a", stars=1, description="d",
            favicon_url=None, favicon_path=None,
            fetched_at=now, source="github",
        ))
        cache.put(CachedItem(
            key="b", stars=2, description="d",
            favicon_url=None, favicon_path=None,
            fetched_at=now, source="github",
        ))
        keys = cache.keys()
        assert set(keys) == {"a", "b"}


class TestParser:
    """Tests for YAML parser."""

    def test_parse_minimal_config(self, tmp_path: Path) -> None:
        """Minimal valid config parses correctly."""
        yaml_content = """
title: Test Landscape
categories: []
"""
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(yaml_content, encoding="utf-8")
        config = parse_landscape_yaml(config_file)
        assert config.title == "Test Landscape"
        assert config.categories == []

    def test_parse_full_config(self, tmp_path: Path) -> None:
        """Full config with categories and items parses correctly."""
        yaml_content = """
title: Test Landscape
categories:
  - name: Category A
    items:
      - name: Tool One
        repo: owner/repo1
        description: First tool
      - name: Tool Two
        url: https://example.com
        description: Second tool
        optional: true
"""
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(yaml_content, encoding="utf-8")
        config = parse_landscape_yaml(config_file)

        assert config.title == "Test Landscape"
        assert len(config.categories) == 1

        cat = config.categories[0]
        assert cat.name == "Category A"
        assert len(cat.items) == 2

        assert cat.items[0].name == "Tool One"
        assert cat.items[0].repo == "owner/repo1"
        assert cat.items[0].description == "First tool"

        assert cat.items[1].name == "Tool Two"
        assert cat.items[1].url == "https://example.com"
        assert cat.items[1].optional is True

    def test_parse_invalid_yaml(self, tmp_path: Path) -> None:
        """Malformed YAML raises YAMLError."""
        yaml_content = """
title: broken
  bad: [indentation
"""
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(yaml_content, encoding="utf-8")
        with pytest.raises(yaml.YAMLError):
            parse_landscape_yaml(config_file)

    def test_parse_root_not_mapping(self, tmp_path: Path) -> None:
        """Root that is not a mapping raises ValueError."""
        yaml_content = """
- item1
- item2
"""
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(yaml_content, encoding="utf-8")
        with pytest.raises(ValueError, match="mapping"):
            parse_landscape_yaml(config_file)


class TestRoundtrip:
    """Tests for config -> YAML -> config roundtrip."""

    def test_roundtrip(self, tmp_path: Path) -> None:
        """Config serialized and re-parsed produces equivalent data."""
        original = LandscapeConfig(
            title="Roundtrip Test",
            categories=[
                LandscapeCategory(
                    name="Category A",
                    subtitle="Sub title",
                    items=[
                        LandscapeItem(
                            name="Tool 1",
                            repo="owner/repo",
                            description="A tool",
                            icon="icon.svg",
                        ),
                    ],
                ),
            ],
        )

        yaml_str = dump_landscape_yaml(original)
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(yaml_str, encoding="utf-8")
        parsed = parse_landscape_yaml(config_file)

        assert parsed.title == original.title
        assert parsed.category_count() == original.category_count()
        assert len(parsed.categories[0].items) == 1
        assert parsed.categories[0].items[0].name == "Tool 1"
        assert parsed.categories[0].items[0].icon == "icon.svg"

    def test_roundtrip_with_groups(self, tmp_path: Path) -> None:
        """Config with sub-groups serializes and re-parses correctly."""
        original = LandscapeConfig(
            title="Group Test",
            categories=[
                LandscapeCategory(
                    name="Skills",
                    groups=[
                        LandscapeSubGroup(
                            name="Skill Reference",
                            items=[
                                LandscapeItem(name="Agent Skills", url="https://agentskills.io"),
                            ],
                        ),
                        LandscapeSubGroup(
                            name="Skill Security Scanners",
                            items=[
                                LandscapeItem(name="DefenseClaw", repo="cisco-ai-defense/defenseclaw"),
                                LandscapeItem(name="SkillSpector", repo="nvidia/skillspector"),
                            ],
                        ),
                    ],
                ),
            ],
        )

        yaml_str = dump_landscape_yaml(original)
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(yaml_str, encoding="utf-8")
        parsed = parse_landscape_yaml(config_file)

        assert parsed.categories[0].has_groups
        assert len(parsed.categories[0].groups) == 2
        assert parsed.categories[0].groups[0].name == "Skill Reference"
        assert len(parsed.categories[0].groups[0].items) == 1
        assert parsed.categories[0].groups[1].name == "Skill Security Scanners"
        assert len(parsed.categories[0].groups[1].items) == 2
        assert parsed.item_count() == 3

    def test_roundtrip_yaml_contains_no_ui_keys(self) -> None:
        """Serialized YAML must not contain page, color, or stroke keys."""
        config = LandscapeConfig(
            title="Clean YAML Test",
            categories=[
                LandscapeCategory(
                    name="Cat",
                    items=[LandscapeItem(name="Tool", repo="owner/repo")],
                ),
            ],
        )
        yaml_str = dump_landscape_yaml(config)
        assert "color" not in yaml_str
        assert "stroke" not in yaml_str
        assert "page:" not in yaml_str
        assert "width:" not in yaml_str
        assert "height:" not in yaml_str


class TestLandscapeSubGroup:
    """Tests for LandscapeSubGroup model."""

    def test_subgroup_basic(self) -> None:
        """Sub-group holds a name and a list of items."""
        item = LandscapeItem(name="Agent Skills", url="https://agentskills.io")
        group = LandscapeSubGroup(name="Skill Reference", items=[item])
        assert group.name == "Skill Reference"
        assert len(group.items) == 1
        assert group.items[0].name == "Agent Skills"

    def test_category_has_groups_true(self) -> None:
        """has_groups is True when groups list is non-empty."""
        cat = LandscapeCategory(
            name="Skills",
            groups=[LandscapeSubGroup(name="G", items=[LandscapeItem(name="X")])],
        )
        assert cat.has_groups is True

    def test_category_has_groups_false(self) -> None:
        """has_groups is False for a flat category."""
        cat = LandscapeCategory(name="Flat", items=[LandscapeItem(name="X")])
        assert cat.has_groups is False

    def test_all_items_flat(self) -> None:
        """all_items equals items for a flat category."""
        items = [LandscapeItem(name="A"), LandscapeItem(name="B")]
        cat = LandscapeCategory(name="C", items=items)
        assert cat.all_items == items

    def test_all_items_grouped(self) -> None:
        """all_items aggregates every item across all sub-groups."""
        cat = LandscapeCategory(
            name="Skills",
            groups=[
                LandscapeSubGroup(name="G1", items=[LandscapeItem(name="X")]),
                LandscapeSubGroup(name="G2", items=[LandscapeItem(name="Y"), LandscapeItem(name="Z")]),
            ],
        )
        names = [i.name for i in cat.all_items]
        assert names == ["X", "Y", "Z"]

    def test_all_items_mixed(self) -> None:
        """all_items returns direct items first, then sub-group items."""
        cat = LandscapeCategory(
            name="C",
            items=[LandscapeItem(name="Direct")],
            groups=[LandscapeSubGroup(name="G", items=[LandscapeItem(name="Grouped")])],
        )
        names = [i.name for i in cat.all_items]
        assert names == ["Direct", "Grouped"]

    def test_item_count_includes_groups(self) -> None:
        """LandscapeConfig.item_count() counts sub-group items."""
        config = LandscapeConfig(
            title="T",
            categories=[
                LandscapeCategory(
                    name="Skills",
                    groups=[
                        LandscapeSubGroup(name="G1", items=[LandscapeItem(name="A")]),
                        LandscapeSubGroup(name="G2", items=[LandscapeItem(name="B"), LandscapeItem(name="C")]),
                    ],
                ),
            ],
        )
        assert config.item_count() == 3

    def test_github_items_includes_groups(self) -> None:
        """LandscapeConfig.github_items() includes sub-group GitHub items."""
        config = LandscapeConfig(
            title="T",
            categories=[
                LandscapeCategory(
                    name="Skills",
                    groups=[
                        LandscapeSubGroup(
                            name="G",
                            items=[
                                LandscapeItem(name="GH", repo="owner/repo"),
                                LandscapeItem(name="URL", url="https://example.com"),
                            ],
                        ),
                    ],
                ),
            ],
        )
        result = config.github_items()
        assert len(result) == 1
        assert result[0][1].name == "GH"


class TestParserGroups:
    """Parser tests specific to the groups key."""

    def test_parse_groups_key(self, tmp_path: Path) -> None:
        """YAML with groups: key produces a grouped category."""
        yaml_content = """
title: Test
categories:
  - name: Skills
    groups:
      - name: Skill Reference
        items:
          - name: Agent Skills
            url: https://agentskills.io
      - name: Skill Security Scanners
        items:
          - name: DefenseClaw
            repo: cisco-ai-defense/defenseclaw
          - name: SkillSpector
            repo: nvidia/skillspector
"""
        f = tmp_path / "l.yaml"
        f.write_text(yaml_content, encoding="utf-8")
        config = parse_landscape_yaml(f)

        cat = config.categories[0]
        assert cat.has_groups
        assert not cat.items  # no flat items
        assert len(cat.groups) == 2
        assert cat.groups[0].name == "Skill Reference"
        assert cat.groups[0].items[0].name == "Agent Skills"
        assert cat.groups[1].name == "Skill Security Scanners"
        assert len(cat.groups[1].items) == 2
        assert config.item_count() == 3
