"""Tests for landscape validator."""

from __future__ import annotations

from tools.landscape.models import (
    LandscapeCategory,
    LandscapeConfig,
    LandscapeItem,
)
from tools.landscape.validator import (
    ValidationResult,
    ValidationReport,
    validate_config,
)


class TestValidationReport:
    """Tests for ValidationReport dataclass."""

    def test_empty_report(self) -> None:
        """Empty report should have zero counts."""
        report = ValidationReport(items=[])
        assert report.total == 0
        assert report.ok == 0
        assert report.warnings == 0
        assert report.errors == 0

    def test_report_with_ok_items(self) -> None:
        """Report should count ok items correctly."""
        report = ValidationReport(
            items=[
                ValidationResult(name="A", category="C", ok=True),
                ValidationResult(name="B", category="C", ok=True),
            ]
        )
        assert report.total == 2
        assert report.ok == 2
        assert report.warnings == 0
        assert report.errors == 0

    def test_report_with_warnings(self) -> None:
        """Report should count warnings correctly."""
        report = ValidationReport(
            items=[
                ValidationResult(name="A", category="C", ok=True, warning="warn"),
                ValidationResult(name="B", category="C", ok=True, warning="warn"),
                ValidationResult(name="C", category="C", ok=True),
            ]
        )
        assert report.total == 3
        assert report.ok == 1  # only items with ok=True and no warning
        assert report.warnings == 2
        assert report.errors == 0

    def test_report_with_errors(self) -> None:
        """Report should count errors correctly."""
        report = ValidationReport(
            items=[
                ValidationResult(name="A", category="C", ok=True),
                ValidationResult(name="B", category="C", ok=False, error="err"),
                ValidationResult(name="C", category="C", ok=False, error="err"),
            ]
        )
        assert report.total == 3
        assert report.ok == 1
        assert report.warnings == 0
        assert report.errors == 2

    def test_report_auto_calculates_on_post_init(self) -> None:
        """__post_init__ should auto-calculate counts."""
        items = [
            ValidationResult(name="A", category="C", ok=True),
            ValidationResult(name="B", category="C", ok=False),
        ]
        # Create with manual counts that are wrong
        report = ValidationReport(items=items, total=100, ok=100, errors=100)
        assert report.total == 2
        assert report.ok == 1
        assert report.errors == 1


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_validate_empty_categories(self) -> None:
        """Empty categories list should return error."""
        config = LandscapeConfig(title="Empty", categories=[])
        report = validate_config(config)

        assert report.total == 1
        assert report.errors == 1
        error_msg = report.items[0].error or ""
        assert "No categories defined" in error_msg

    def test_validate_minimal_config(self) -> None:
        """Minimal valid config should pass without GitHub client."""
        config = LandscapeConfig(
            title="Test",
            categories=[
                LandscapeCategory(
                    name="Lang",
                    items=[
                        LandscapeItem(name="Item 1"),
                        LandscapeItem(name="Item 2"),
                    ],
                ),
            ],
        )
        report = validate_config(config)

        assert report.total == 2
        assert report.ok == 0  # items get warnings for missing descriptions
        assert report.warnings == 2  # "No description available" on each
        assert report.errors == 0

    def test_validate_with_github_client(self) -> None:
        """With GitHub client, items with valid repos should be ok."""
        config = LandscapeConfig(
            title="Test",
            categories=[
                LandscapeCategory(
                    name="Lang",
                    items=[
                        LandscapeItem(name="OpenSpec", repo="Fission-AI/OpenSpec"),
                    ],
                ),
            ],
        )
        from tools.landscape.github import GitHubClient
        from tools.landscape.cache import Cache
        from pathlib import Path

        cache = Cache(Path(".landscape-cache.json"))
        gh = GitHubClient(cache=cache)
        report = validate_config(config, github_client=gh)

        assert report.total == 1
        assert report.ok >= 1 or report.warnings >= 1

    def test_validate_empty_category_name(self) -> None:
        """Category with empty name should produce error."""
        config = LandscapeConfig(
            title="Test",
            categories=[
                LandscapeCategory(name=""),
            ],
        )
        report = validate_config(config)

        # Should have error for empty category name
        assert report.errors >= 1

    def test_validate_missing_item_name(self) -> None:
        """Item with empty name should produce error."""
        config = LandscapeConfig(
            title="Test",
            categories=[
                LandscapeCategory(
                    name="Lang",
                    items=[LandscapeItem(name="")],
                ),
            ],
        )
        report = validate_config(config)

        assert report.errors >= 1
        assert report.items[0].error == "Missing item name"

    def test_yaml_description_takes_priority_over_github(self) -> None:
        """YAML description wins over GitHub description when both are present."""
        from unittest.mock import MagicMock
        from tools.landscape.github import GitHubRepoInfo

        config = LandscapeConfig(
            title="Test",
            categories=[
                LandscapeCategory(
                    name="Tools",
                    items=[
                        LandscapeItem(
                            name="MyTool",
                            repo="org/my-tool",
                            description="Description from YAML",
                        ),
                    ],
                ),
            ],
        )

        github_description = "Description from GitHub"
        mock_client = MagicMock()
        mock_client.get_repo_info.return_value = GitHubRepoInfo(
            stars=42,
            description=github_description,
            url="https://github.com/org/my-tool",
            owner="org",
            name="my-tool",
        )

        report = validate_config(config, github_client=mock_client)

        assert report.total == 1
        assert report.items[0].description == "Description from YAML"
        assert report.items[0].description != github_description

    def test_github_description_used_when_yaml_description_absent(self) -> None:
        """GitHub description is used when YAML description is not set."""
        from unittest.mock import MagicMock
        from tools.landscape.github import GitHubRepoInfo

        config = LandscapeConfig(
            title="Test",
            categories=[
                LandscapeCategory(
                    name="Tools",
                    items=[
                        LandscapeItem(
                            name="MyTool",
                            repo="org/my-tool",
                        ),
                    ],
                ),
            ],
        )

        mock_client = MagicMock()
        mock_client.get_repo_info.return_value = GitHubRepoInfo(
            stars=10,
            description="Description from GitHub",
            url="https://github.com/org/my-tool",
            owner="org",
            name="my-tool",
        )

        report = validate_config(config, github_client=mock_client)

        assert report.total == 1
        assert report.items[0].description == "Description from GitHub"

    def test_validate_dry_run(self) -> None:
        """Dry run should skip GitHub lookups."""
        config = LandscapeConfig(
            title="Test",
            categories=[
                LandscapeCategory(
                    name="Lang",
                    items=[
                        LandscapeItem(
                            name="OpenSpec",
                            repo="Fission-AI/OpenSpec",
                        ),
                    ],
                ),
            ],
        )
        report = validate_config(config, dry_run=True)

        # Should not make any network calls
        # Items with repos should get a warning about skipping
        assert report.total == 1
