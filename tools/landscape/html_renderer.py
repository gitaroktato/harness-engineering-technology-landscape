"""HTML renderer for landscape data using Jinja2 templates."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .colors import CATEGORY_PALETTE, _fmt_stars
from .models import LandscapeCategory, LandscapeConfig, LandscapeItem

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"


# ── View-model dataclasses ────────────────────────────────────────────────────


@dataclass
class CardView:
    """View-model for a single technology card."""

    name: str
    repo_short: str
    favicon_url: str | None
    description: str | None
    stars: int | None
    warning: str | None
    link_url: str | None = None

    @property
    def stars_fmt(self) -> str:
        """Format star count for display (e.g. 62.9k)."""
        return _fmt_stars(self.stars)


@dataclass
class PaletteView:
    """Fill / stroke color pair for a category."""

    fill: str
    stroke: str


@dataclass
class SubGroupView:
    """View-model for a sub-group column inside a grouped category."""

    name: str
    cards: list[CardView] = field(default_factory=list)


@dataclass
class CategoryView:
    """View-model for one category section."""

    name: str
    subtitle: str | None
    palette: PaletteView
    has_groups: bool
    cards: list[CardView] = field(default_factory=list)
    groups: list[SubGroupView] = field(default_factory=list)


# ── HTMLRenderer ──────────────────────────────────────────────────────────────


class HTMLRenderer:
    """Renders a LandscapeConfig as a self-contained HTML file.

    The output mirrors the DrawIO diagram's visual design: dark background,
    swimlane rows with the same 6-color palette, and cards with favicons,
    item names, repo slugs, descriptions, and star counts.
    """

    def __init__(self, config: LandscapeConfig) -> None:
        self.config = config
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "j2"]),
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_card(
        self,
        item: LandscapeItem,
        data: dict[str, int | str | None],
    ) -> CardView:
        """Build a CardView from an item and its render data dict."""
        stars = data.get("stars")
        desc = data.get("description")
        warning = data.get("warning")

        return CardView(
            name=item.name,
            repo_short=item.repo_short,
            favicon_url=item.favicon_url or None,
            description=str(desc) if desc is not None else None,
            stars=int(stars) if isinstance(stars, int) else None,
            warning=str(warning) if warning is not None else None,
            link_url=item.url or (f"https://github.com/{item.repo}" if item.repo else None),
        )

    def _build_category_view(
        self,
        cat: LandscapeCategory,
        idx: int,
        items_with_data: dict[tuple[str, str], dict[str, int | str | None]],
    ) -> CategoryView:
        """Assemble the full CategoryView for a category."""
        fill, stroke = CATEGORY_PALETTE[idx % len(CATEGORY_PALETTE)]
        palette = PaletteView(fill=fill, stroke=stroke)

        if cat.has_groups:
            groups: list[SubGroupView] = []
            for group in cat.groups:
                subgroup_view = SubGroupView(name=group.name)
                for item in group.items:
                    data = items_with_data.get((cat.name, item.name), {})
                    subgroup_view.cards.append(self._build_card(item, data))
                groups.append(subgroup_view)
            return CategoryView(
                name=cat.name,
                subtitle=cat.subtitle,
                palette=palette,
                has_groups=True,
                groups=groups,
            )

        cards: list[CardView] = []
        for item in cat.items:
            data = items_with_data.get((cat.name, item.name), {})
            cards.append(self._build_card(item, data))

        return CategoryView(
            name=cat.name,
            subtitle=cat.subtitle,
            palette=palette,
            has_groups=False,
            cards=cards,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def render(
        self,
        items_with_data: dict[tuple[str, str], dict[str, int | str | None]],
        output: IO[str] | Path | None = None,
    ) -> str:
        """Render the full HTML page.

        Args:
            items_with_data: Mapping of (category_name, item_name) ->
                {stars: int|None, description: str|None, warning: str|None}.
            output: Optional file path or open file object to write to.

        Returns:
            The rendered HTML string.
        """
        categories = [
            self._build_category_view(cat, idx, items_with_data)
            for idx, cat in enumerate(self.config.categories)
        ]

        template = self._env.get_template("landscape.html.j2")
        html = template.render(title=self.config.title, categories=categories)

        if output is not None:
            if isinstance(output, Path):
                output.write_text(html, encoding="utf-8")
                logger.info("Wrote HTML to %s", output)
            else:
                output.write(html)

        return html
