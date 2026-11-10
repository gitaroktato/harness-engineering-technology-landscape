"""Validation logic for landscape data."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .github import GitHubClient
from .models import LandscapeCategory, LandscapeConfig

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a single item."""

    name: str
    category: str
    ok: bool
    stars: int | None = None
    description: str | None = None
    warning: str | None = None
    error: str | None = None


@dataclass
class ValidationReport:
    """Report from validating the full landscape."""

    items: list[ValidationResult] = None  # type: ignore[assignment]
    total: int = 0
    ok: int = 0
    warnings: int = 0
    errors: int = 0

    def __post_init__(self) -> None:
        if self.items is None:
            self.items = []
        self.total = len(self.items)
        self.ok = sum(1 for i in self.items if i.ok and not i.warning)
        self.warnings = sum(
            1 for i in self.items if i.ok and i.warning
        )
        self.errors = sum(1 for i in self.items if not i.ok)

    def as_render_data(self) -> dict[tuple[str, str], dict[str, Any]]:
        """Return a renderer-ready mapping of (category, name) -> item data.

        Args:
            None

        Returns:
            Dict keyed by (category, name) tuples with stars, description,
            and optional warning/error fields.
        """
        result: dict[tuple[str, str], dict[str, Any]] = {}
        for item in self.items:
            key = (item.category, item.name)
            data: dict[str, Any] = {
                "stars": item.stars,
                "description": item.description,
            }
            if item.warning:
                data["warning"] = item.warning
            if item.error:
                data["error"] = item.error
            result[key] = data
        return result


def validate_config(
    config: LandscapeConfig,
    github_client: GitHubClient | None = None,
    dry_run: bool = False,
) -> ValidationReport:
    """Validate the entire landscape configuration.

    Checks:
    - All items have a name
    - GitHub repos exist
    - Descriptions are meaningful
    - Star counts are numeric

    Args:
        config: The landscape configuration to validate.
        github_client: Optional GitHub client for repo checks.
        dry_run: If True, skip actual GitHub lookups.

    Returns:
        ValidationReport with results for all items.
    """
    report = ValidationReport()

    # Validate category structure
    if not config.categories:
        report.items.append(
            ValidationResult(
                name="(root)",
                category="",
                ok=False,
                error="No categories defined",
            )
        )
        # No categories to process, return early
        report.total = 1
        report.ok = 0
        report.warnings = 0
        report.errors = 1
        return report

    for cat in config.categories:
        if not cat.name.strip():
            report.items.append(
                ValidationResult(
                    name="(root)",
                    category="",
                    ok=False,
                    error="Category has empty name",
                )
            )

        for item in cat.all_items:
            result = ValidationResult(
                name=item.name,
                category=cat.name,
                ok=True,
            )

            # Check name
            if not item.name.strip():
                result.ok = False
                result.error = "Missing item name"
                report.items.append(result)
                continue

            # Check GitHub repo if specified
            if item.repo:
                if github_client:
                    repo_key = item.github_key
                    if repo_key:
                        owner, repo = repo_key.split("/", 1)
                        repo_info = github_client.get_repo_info(owner, repo)

                        if repo_info is None:
                            if item.optional:
                                result.warning = f"GitHub lookup failed for {repo_key} (optional item, skipped)"
                            else:
                                result.ok = False
                                result.error = f"GitHub lookup failed for {repo_key}"
                        elif not repo_info.exists:
                            if item.optional:
                                result.warning = (
                                    f"Repo {repo_key} does not exist (optional)"
                                )
                            else:
                                result.ok = False
                                result.error = f"Repo {repo_key} does not exist"
                        elif repo_info.is_private:
                            result.warning = f"Repo {repo_key} is private"
                            result.stars = 0
                            result.description = item.description or repo_info.description or ""
                        else:
                            result.stars = repo_info.stars
                            result.description = item.description or repo_info.description or ""
                    else:
                        result.warning = (
                            f"Invalid repo format: {item.repo} (expected owner/repo)"
                        )
                else:
                    result.warning = "No GitHub client provided, skipping repo validation"

            # For URL-only items (no repo), populate description from YAML.
            # For repo-backed items this is already set above, but if the
            # GitHub branch was skipped (no client, dry-run, lookup failed)
            # result.description is still None — fill it from YAML here too.
            if result.description is None:
                result.description = item.description
            if not result.description:
                result.warning = "No description available"

            # Check star count for GitHub repos
            if item.is_github and result.stars is not None and result.stars < 0:
                result.ok = False
                result.error = "Invalid star count"

            report.items.append(result)

    # Recalculate summary counts after all items are appended
    report.total = len(report.items)
    report.ok = sum(1 for i in report.items if i.ok and not i.warning)
    report.warnings = sum(1 for i in report.items if i.ok and i.warning)
    report.errors = sum(1 for i in report.items if not i.ok)
    return report
