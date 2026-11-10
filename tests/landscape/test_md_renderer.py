"""Tests for MarkdownRenderer."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from tools.landscape.md_renderer import MarkdownRenderer, _item_link
from tools.landscape.models import (
    LandscapeCategory,
    LandscapeConfig,
    LandscapeItem,
    LandscapeSubGroup,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_flat_config() -> LandscapeConfig:
    return LandscapeConfig(
        title="Test Landscape",
        categories=[
            LandscapeCategory(
                name="Orchestration",
                items=[
                    LandscapeItem(
                        name="Symphony",
                        repo="openai/symphony",
                        description="Isolated autonomous runs",
                    ),
                    LandscapeItem(
                        name="pi.dev",
                        url="https://pi.dev/",
                        description="Minimal agent harness",
                    ),
                ],
            ),
        ],
    )


def _make_subtitle_config() -> LandscapeConfig:
    return LandscapeConfig(
        title="Test",
        categories=[
            LandscapeCategory(
                name="SDD",
                subtitle="Spec-Driven Development",
                items=[
                    LandscapeItem(name="OpenSpec", repo="Fission-AI/OpenSpec"),
                ],
            ),
        ],
    )


def _make_grouped_config() -> LandscapeConfig:
    return LandscapeConfig(
        title="Grouped",
        categories=[
            LandscapeCategory(
                name="Working with Skills",
                groups=[
                    LandscapeSubGroup(
                        name="Skill Reference",
                        items=[
                            LandscapeItem(
                                name="Agent Skills",
                                url="https://agentskills.io/home",
                                description="Open format for agent skills",
                            )
                        ],
                    ),
                    LandscapeSubGroup(
                        name="Skill Security Scanners",
                        items=[
                            LandscapeItem(
                                name="DefenseClaw",
                                repo="cisco-ai-defense/defenseclaw",
                                description="Security governance",
                            ),
                            LandscapeItem(
                                name="SkillSpector",
                                repo="nvidia/skillspector",
                                description="Scanner for agent skills",
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _make_no_link_config() -> LandscapeConfig:
    """Item with neither repo nor url."""
    return LandscapeConfig(
        title="NoLink",
        categories=[
            LandscapeCategory(
                name="Tools",
                items=[
                    LandscapeItem(
                        name="MysteriousTool",
                        description="Has no URL at all",
                    )
                ],
            ),
        ],
    )


# ── _item_link helper ──────────────────────────────────────────────────────────


class TestItemLink:
    def test_url_takes_priority_over_repo(self) -> None:
        item = LandscapeItem(
            name="X",
            url="https://example.com",
            repo="owner/repo",
        )
        assert _item_link(item) == "https://example.com"

    def test_repo_used_when_no_url(self) -> None:
        item = LandscapeItem(name="X", repo="openai/symphony")
        assert _item_link(item) == "https://github.com/openai/symphony"

    def test_empty_string_when_neither(self) -> None:
        item = LandscapeItem(name="X")
        assert _item_link(item) == ""


# ── MarkdownRenderer basic output ─────────────────────────────────────────────


class TestMarkdownRendererOutput:
    def test_render_returns_str(self) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        result = renderer.render()
        assert isinstance(result, str)

    def test_render_contains_h1_title(self) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        result = renderer.render()
        assert "# Harness Engineering - Technology Landscape" in result

    def test_render_contains_intro_paragraph(self) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        result = renderer.render()
        assert "Agent = Model + Harness" in result

    def test_render_contains_category_h2(self) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        result = renderer.render()
        assert "## Orchestration" in result

    def test_render_contains_item_names(self) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        result = renderer.render()
        assert "Symphony" in result
        assert "pi.dev" in result

    def test_render_contains_item_descriptions(self) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        result = renderer.render()
        assert "Isolated autonomous runs" in result
        assert "Minimal agent harness" in result

    def test_render_contains_references_section(self) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        result = renderer.render()
        assert "## References" in result

    def test_render_contains_hardcoded_reference_urls(self) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        result = renderer.render()
        assert "awesome-harness-engineering" in result
        assert "kaggle.com" in result

    def test_render_contains_article_links_in_references(self) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        result = renderer.render()
        assert "Google Cloud Blog" in result
        assert "Karpathy" in result


# ── Link generation ────────────────────────────────────────────────────────────


class TestMarkdownRendererLinks:
    def test_repo_item_gets_github_url(self) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        result = renderer.render()
        assert "[Symphony](https://github.com/openai/symphony)" in result

    def test_url_item_uses_explicit_url(self) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        result = renderer.render()
        assert "[pi.dev](https://pi.dev/)" in result

    def test_item_with_both_url_and_repo_uses_url(self) -> None:
        config = LandscapeConfig(
            title="T",
            categories=[
                LandscapeCategory(
                    name="Cat",
                    items=[
                        LandscapeItem(
                            name="Dual",
                            url="https://example.com",
                            repo="owner/repo",
                            description="desc",
                        )
                    ],
                )
            ],
        )
        renderer = MarkdownRenderer(config)
        result = renderer.render()
        assert "[Dual](https://example.com)" in result
        assert "github.com/owner/repo" not in result

    def test_item_without_link_renders_plain_name(self) -> None:
        renderer = MarkdownRenderer(_make_no_link_config())
        result = renderer.render()
        assert "- MysteriousTool" in result
        # Should NOT be a markdown link
        assert "[MysteriousTool](" not in result

    def test_item_without_link_still_shows_description(self) -> None:
        renderer = MarkdownRenderer(_make_no_link_config())
        result = renderer.render()
        assert "Has no URL at all" in result


# ── Subtitle ──────────────────────────────────────────────────────────────────


class TestMarkdownRendererSubtitle:
    def test_subtitle_renders_as_h3(self) -> None:
        renderer = MarkdownRenderer(_make_subtitle_config())
        result = renderer.render()
        assert "### Spec-Driven Development" in result

    def test_category_with_subtitle_renders_h2_name(self) -> None:
        renderer = MarkdownRenderer(_make_subtitle_config())
        result = renderer.render()
        assert "## SDD" in result

    def test_no_subtitle_no_h3_for_category(self) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        result = renderer.render()
        # No subtitle set in flat config — no ### heading for the category itself
        assert "### Orchestration" not in result


# ── Grouped categories ────────────────────────────────────────────────────────


class TestMarkdownRendererGroups:
    def test_category_with_groups_renders_h2(self) -> None:
        renderer = MarkdownRenderer(_make_grouped_config())
        result = renderer.render()
        assert "## Working with Skills" in result

    def test_group_names_render_as_h3(self) -> None:
        renderer = MarkdownRenderer(_make_grouped_config())
        result = renderer.render()
        assert "### Skill Reference" in result
        assert "### Skill Security Scanners" in result

    def test_group_item_names_appear(self) -> None:
        renderer = MarkdownRenderer(_make_grouped_config())
        result = renderer.render()
        assert "Agent Skills" in result
        assert "DefenseClaw" in result
        assert "SkillSpector" in result

    def test_group_items_have_correct_links(self) -> None:
        renderer = MarkdownRenderer(_make_grouped_config())
        result = renderer.render()
        assert "[Agent Skills](https://agentskills.io/home)" in result
        assert (
            "[DefenseClaw](https://github.com/cisco-ai-defense/defenseclaw)" in result
        )

    def test_group_items_have_descriptions(self) -> None:
        renderer = MarkdownRenderer(_make_grouped_config())
        result = renderer.render()
        assert "Security governance" in result
        assert "Scanner for agent skills" in result


# ── Empty categories are skipped ──────────────────────────────────────────────


class TestMarkdownRendererEmptyCategory:
    def test_empty_category_not_rendered(self) -> None:
        config = LandscapeConfig(
            title="T",
            categories=[
                LandscapeCategory(name="References", items=[]),
            ],
        )
        renderer = MarkdownRenderer(config)
        result = renderer.render()
        # The empty References category from YAML should not produce a ## heading
        # (References is hardcoded in the template footer)
        lines = result.splitlines()
        references_headings = [l for l in lines if l == "## References"]
        # Only the hardcoded one at the end should appear, not from the empty cat
        assert len(references_headings) == 1

    def test_empty_config_renders_without_error(self) -> None:
        config = LandscapeConfig(title="Empty", categories=[])
        renderer = MarkdownRenderer(config)
        result = renderer.render()
        assert "# Harness Engineering" in result
        assert "## References" in result


# ── File output ───────────────────────────────────────────────────────────────


class TestMarkdownRendererFileOutput:
    def test_render_to_path(self, tmp_path: Path) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        out = tmp_path / "landscape.md"
        returned = renderer.render(out)
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert content == returned
        assert "# Harness Engineering" in content

    def test_render_creates_parent_dirs(self, tmp_path: Path) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        out = tmp_path / "nested" / "dir" / "landscape.md"
        renderer.render(out)
        assert out.exists()

    def test_render_to_file_object(self, tmp_path: Path) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        buf = io.StringIO()
        returned = renderer.render(buf)
        buf.seek(0)
        assert buf.read() == returned
        assert "# Harness Engineering" in returned

    def test_render_none_output_returns_str_only(self) -> None:
        renderer = MarkdownRenderer(_make_flat_config())
        result = renderer.render(None)
        assert isinstance(result, str)
        assert len(result) > 0


# ── CLI markdown command ───────────────────────────────────────────────────────


class TestCLIMarkdownCommand:
    def test_markdown_command_creates_file(self, tmp_path: Path) -> None:
        from click.testing import CliRunner
        from tools.landscape.cli import main

        # Write a minimal config
        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(
            "title: CLI Test\ncategories:\n  - name: Tools\n    items:\n"
            "      - name: MyTool\n        repo: owner/repo\n"
            "        description: A test tool\n",
            encoding="utf-8",
        )
        output_file = tmp_path / "out.md"
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["markdown", "--config", str(config_file), "--output", str(output_file)],
        )
        assert result.exit_code == 0, result.output
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "MyTool" in content
        assert "https://github.com/owner/repo" in content

    def test_markdown_command_prints_output_path(self, tmp_path: Path) -> None:
        from click.testing import CliRunner
        from tools.landscape.cli import main

        config_file = tmp_path / "landscape.yaml"
        config_file.write_text(
            "title: CLI Test\ncategories: []\n",
            encoding="utf-8",
        )
        output_file = tmp_path / "out.md"
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["markdown", "--config", str(config_file), "--output", str(output_file)],
        )
        assert "Output:" in result.output
        assert str(output_file) in result.output
