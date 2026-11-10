"""Tests for HTMLRenderer."""

from __future__ import annotations

from pathlib import Path

from tools.landscape.html_renderer import CardView, HTMLRenderer
from tools.landscape.models import (
    LandscapeCategory,
    LandscapeConfig,
    LandscapeItem,
    LandscapeSubGroup,
)
from tools.landscape.colors import CATEGORY_PALETTE

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_config() -> LandscapeConfig:
    return LandscapeConfig(
        title="Test Landscape",
        categories=[
            LandscapeCategory(
                name="SDD",
                items=[
                    LandscapeItem(name="OpenSpec", repo="Fission-AI/OpenSpec"),
                    LandscapeItem(name="spec-kit", repo="github/spec-kit"),
                ],
            ),
        ],
    )


def _make_grouped_config() -> LandscapeConfig:
    return LandscapeConfig(
        title="Grouped Landscape",
        categories=[
            LandscapeCategory(
                name="Skills",
                groups=[
                    LandscapeSubGroup(
                        name="Skill Reference",
                        items=[LandscapeItem(name="AgentSkills", url="https://agentskills.io")],
                    ),
                    LandscapeSubGroup(
                        name="Security Scanners",
                        items=[
                            LandscapeItem(name="DefenseClaw", repo="cisco/defenseclaw"),
                            LandscapeItem(name="SkillSpector", repo="nvidia/skillspector"),
                        ],
                    ),
                ],
            ),
        ],
    )


_EMPTY_DATA: dict[tuple[str, str], dict[str, int | str | None]] = {}


# ── CardView unit tests ───────────────────────────────────────────────────────


class TestCardView:
    def test_stars_fmt_thousands(self) -> None:
        card = CardView(
            name="X", repo_short="a/b", favicon_url=None,
            description=None, stars=62900, warning=None,
        )
        assert card.stars_fmt == "62.9k"

    def test_stars_fmt_none(self) -> None:
        card = CardView(
            name="X", repo_short="a/b", favicon_url=None,
            description=None, stars=None, warning=None,
        )
        assert card.stars_fmt == "?"

    def test_stars_fmt_small(self) -> None:
        card = CardView(
            name="X", repo_short="a/b", favicon_url=None,
            description=None, stars=42, warning=None,
        )
        assert card.stars_fmt == "42"


# ── HTMLRenderer basic structure ──────────────────────────────────────────────


class TestHTMLRendererStructure:
    def test_render_returns_str(self) -> None:
        renderer = HTMLRenderer(_make_config())
        result = renderer.render(_EMPTY_DATA)
        assert isinstance(result, str)

    def test_render_starts_with_doctype(self) -> None:
        renderer = HTMLRenderer(_make_config())
        result = renderer.render(_EMPTY_DATA)
        assert result.strip().startswith("<!DOCTYPE html>")

    def test_render_contains_title(self) -> None:
        renderer = HTMLRenderer(_make_config())
        result = renderer.render(_EMPTY_DATA)
        assert "Test Landscape" in result

    def test_render_contains_category_name(self) -> None:
        renderer = HTMLRenderer(_make_config())
        result = renderer.render(_EMPTY_DATA)
        assert "SDD" in result

    def test_render_contains_item_names(self) -> None:
        renderer = HTMLRenderer(_make_config())
        result = renderer.render(_EMPTY_DATA)
        assert "OpenSpec" in result
        assert "spec-kit" in result

    def test_render_contains_repo_short(self) -> None:
        renderer = HTMLRenderer(_make_config())
        result = renderer.render(_EMPTY_DATA)
        assert "Fission-AI/OpenSpec" in result

    def test_render_contains_stars(self) -> None:
        renderer = HTMLRenderer(_make_config())
        data: dict[tuple[str, str], dict[str, int | str | None]] = {
            ("SDD", "OpenSpec"): {"stars": 58900, "description": "AI spec tool"},
        }
        result = renderer.render(data)
        assert "58.9k" in result

    def test_render_contains_description(self) -> None:
        renderer = HTMLRenderer(_make_config())
        data: dict[tuple[str, str], dict[str, int | str | None]] = {
            ("SDD", "OpenSpec"): {"stars": 100, "description": "Spec-driven AI tool"},
        }
        result = renderer.render(data)
        assert "Spec-driven AI tool" in result

    def test_render_contains_warning(self) -> None:
        renderer = HTMLRenderer(_make_config())
        data: dict[tuple[str, str], dict[str, int | str | None]] = {
            ("SDD", "OpenSpec"): {"stars": 100, "description": "desc", "warning": "Repo archived"},
        }
        result = renderer.render(data)
        assert "Repo archived" in result

    def test_render_no_stars_section_when_none(self) -> None:
        renderer = HTMLRenderer(_make_config())
        result = renderer.render(_EMPTY_DATA)
        # Stars section is only rendered when stars is not None.
        # The CSS class "card-stars" appears in <style>, but the div element
        # should not be present when there is no star data.
        assert '<div class="card-stars">' not in result

    def test_render_contains_favicon_img_tag(self) -> None:
        renderer = HTMLRenderer(_make_config())
        result = renderer.render(_EMPTY_DATA)
        # GitHub items get github.com favicon
        assert "github.com/favicon.ico" in result

    def test_render_to_file(self, tmp_path: Path) -> None:
        renderer = HTMLRenderer(_make_config())
        out = tmp_path / "landscape.html"
        renderer.render(_EMPTY_DATA, output=out)
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_render_to_file_object(self, tmp_path: Path) -> None:
        renderer = HTMLRenderer(_make_config())
        out = tmp_path / "landscape.html"
        with out.open("w", encoding="utf-8") as fh:
            renderer.render(_EMPTY_DATA, output=fh)
        assert out.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")


# ── Palette & colors ──────────────────────────────────────────────────────────


class TestHTMLRendererColors:
    def test_first_category_uses_first_palette_color(self) -> None:
        renderer = HTMLRenderer(_make_config())
        result = renderer.render(_EMPTY_DATA)
        fill, stroke = CATEGORY_PALETTE[0]
        assert fill in result
        assert stroke in result

    def test_second_category_uses_second_palette_color(self) -> None:
        config = LandscapeConfig(
            title="T",
            categories=[
                LandscapeCategory(name="Cat1", items=[LandscapeItem(name="A", repo="a/b")]),
                LandscapeCategory(name="Cat2", items=[LandscapeItem(name="B", repo="c/d")]),
            ],
        )
        renderer = HTMLRenderer(config)
        result = renderer.render(_EMPTY_DATA)
        _, stroke1 = CATEGORY_PALETTE[0]
        _, stroke2 = CATEGORY_PALETTE[1]
        assert stroke1 in result
        assert stroke2 in result

    def test_palette_round_robin_beyond_six(self) -> None:
        """Seven categories should wrap the palette (index 6 → palette[0])."""
        categories = [
            LandscapeCategory(name=f"Cat{i}", items=[LandscapeItem(name=f"I{i}", repo=f"a/{i}")])
            for i in range(7)
        ]
        config = LandscapeConfig(title="T", categories=categories)
        renderer = HTMLRenderer(config)
        result = renderer.render(_EMPTY_DATA)
        # All 6 palette fill colors should appear
        for fill, _ in CATEGORY_PALETTE:
            assert fill in result


# ── Subtitle ──────────────────────────────────────────────────────────────────


class TestHTMLRendererSubtitle:
    def test_subtitle_appears(self) -> None:
        config = LandscapeConfig(
            title="T",
            categories=[
                LandscapeCategory(
                    name="SDD",
                    subtitle="Spec-Driven Development",
                    items=[LandscapeItem(name="X", repo="a/b")],
                ),
            ],
        )
        renderer = HTMLRenderer(config)
        result = renderer.render(_EMPTY_DATA)
        assert "Spec-Driven Development" in result

    def test_no_subtitle_renders_name_only(self) -> None:
        renderer = HTMLRenderer(_make_config())
        result = renderer.render(_EMPTY_DATA)
        # subtitle mdash separator should not appear when no subtitle
        assert "&mdash;" not in result


# ── Grouped categories ────────────────────────────────────────────────────────


class TestHTMLRendererGroups:
    def test_group_names_appear(self) -> None:
        renderer = HTMLRenderer(_make_grouped_config())
        result = renderer.render(_EMPTY_DATA)
        assert "Skill Reference" in result
        assert "Security Scanners" in result

    def test_group_item_names_appear(self) -> None:
        renderer = HTMLRenderer(_make_grouped_config())
        result = renderer.render(_EMPTY_DATA)
        assert "AgentSkills" in result
        assert "DefenseClaw" in result
        assert "SkillSpector" in result

    def test_groups_row_class_present(self) -> None:
        renderer = HTMLRenderer(_make_grouped_config())
        result = renderer.render(_EMPTY_DATA)
        assert "groups-row" in result

    def test_flat_category_uses_items_row(self) -> None:
        renderer = HTMLRenderer(_make_config())
        result = renderer.render(_EMPTY_DATA)
        assert "items-row" in result

    def test_grouped_category_does_not_use_items_row(self) -> None:
        renderer = HTMLRenderer(_make_grouped_config())
        result = renderer.render(_EMPTY_DATA)
        # The div element with class "items-row" should not be present in
        # grouped categories. The CSS class name appears in <style> but not
        # as an actual element when only grouped categories exist.
        assert '<div class="items-row">' not in result


# ── Multiple categories ───────────────────────────────────────────────────────


class TestHTMLRendererMultipleCategories:
    def test_all_category_names_appear(self) -> None:
        config = LandscapeConfig(
            title="Multi",
            categories=[
                LandscapeCategory(name="Alpha", items=[LandscapeItem(name="X", repo="a/b")]),
                LandscapeCategory(name="Beta", items=[LandscapeItem(name="Y", repo="c/d")]),
                LandscapeCategory(name="Gamma", items=[LandscapeItem(name="Z", repo="e/f")]),
            ],
        )
        renderer = HTMLRenderer(config)
        result = renderer.render(_EMPTY_DATA)
        assert "Alpha" in result
        assert "Beta" in result
        assert "Gamma" in result


# ── Empty config ──────────────────────────────────────────────────────────────


class TestHTMLRendererEdgeCases:
    def test_empty_config_renders_without_error(self) -> None:
        config = LandscapeConfig(title="Empty", categories=[])
        renderer = HTMLRenderer(config)
        result = renderer.render(_EMPTY_DATA)
        assert "Empty" in result
        assert "<!DOCTYPE html>" in result

    def test_empty_category_renders_without_error(self) -> None:
        config = LandscapeConfig(
            title="T",
            categories=[LandscapeCategory(name="Empty", items=[])],
        )
        renderer = HTMLRenderer(config)
        result = renderer.render(_EMPTY_DATA)
        assert "Empty" in result

    def test_item_without_repo_shows_hostname(self) -> None:
        """URL-only items display the hostname, not N/A, in the repo slot."""
        from tools.landscape.validator import validate_config

        config = LandscapeConfig(
            title="T",
            categories=[
                LandscapeCategory(
                    name="Tools",
                    items=[
                        LandscapeItem(
                            name="FancyTool",
                            url="https://fancy.tool/some/path",
                            description="A fancy tool",
                        )
                    ],
                ),
            ],
        )
        report = validate_config(config, github_client=None, dry_run=True)
        result = HTMLRenderer(config).render(report.as_render_data())
        assert "fancy.tool" in result
        assert "N/A" not in result

    def test_item_without_repo_or_url_renders_na(self) -> None:
        """Items with neither a repo nor a URL still show N/A."""
        config = LandscapeConfig(
            title="T",
            categories=[
                LandscapeCategory(
                    name="Tools",
                    items=[LandscapeItem(name="Mystery")],
                ),
            ],
        )
        renderer = HTMLRenderer(config)
        result = renderer.render(_EMPTY_DATA)
        assert "N/A" in result

    def test_url_only_item_with_yaml_description_shows_description(self) -> None:
        """URL-only items with a YAML description show it after validation."""
        from tools.landscape.validator import validate_config

        config = LandscapeConfig(
            title="T",
            categories=[
                LandscapeCategory(
                    name="Tools",
                    items=[
                        LandscapeItem(
                            name="Fabro",
                            url="https://docs.fabro.sh/getting-started/introduction",
                            description="Version-controlled workflow graphs",
                        )
                    ],
                ),
            ],
        )
        report = validate_config(config, github_client=None, dry_run=True)
        items_with_data = report.as_render_data()
        renderer = HTMLRenderer(config)
        result = renderer.render(items_with_data)
        assert "Version-controlled workflow graphs" in result
        assert "docs.fabro.sh" in result

    def test_description_na_when_missing(self) -> None:
        renderer = HTMLRenderer(_make_config())
        result = renderer.render(_EMPTY_DATA)
        # Items with no data get "N/A" from the template's `or "N/A"` filter
        assert "N/A" in result
