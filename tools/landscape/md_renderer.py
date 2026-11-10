"""Markdown renderer for landscape data using Jinja2 templates."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import IO

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import LandscapeConfig, LandscapeItem

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _item_link(item: LandscapeItem) -> str:
    """Return the best hyperlink URL for a landscape item.

    Priority:
    1. Explicit ``url`` field
    2. Constructed GitHub URL from ``repo``
    3. Empty string (item will render without a link)
    """
    if item.url:
        return item.url
    if item.repo:
        return f"https://github.com/{item.repo}"
    return ""


class MarkdownRenderer:
    """Renders a :class:`LandscapeConfig` as a Markdown document.

    The output mirrors the structure of ``technology-landscape.md``:
    top-level ``##`` sections per category, ``###`` subtitles / sub-group
    headers where applicable, and a bullet list of linked items per section.

    The introductory prose paragraph and the References section are hardcoded
    in the Jinja2 template (``landscape.md.j2``) because they are not part of
    the structured YAML config.
    """

    def __init__(self, config: LandscapeConfig) -> None:
        """Initialise the renderer.

        Args:
            config: Parsed landscape configuration.
        """
        self.config = config
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape([]),  # No HTML escaping for Markdown
            keep_trailing_newline=True,
            trim_blocks=True,   # Remove the first newline after a block tag
            lstrip_blocks=True, # Strip leading whitespace from block tags
        )
        self._env.globals["item_link"] = _item_link

    def render(self, output: IO[str] | Path | None = None) -> str:
        """Render the full Markdown document.

        Args:
            output: Optional file path or open file object to write to.
                When *output* is a :class:`~pathlib.Path` the parent
                directory is created automatically if it does not exist.

        Returns:
            The rendered Markdown string.
        """
        template = self._env.get_template("landscape.md.j2")
        md = template.render(
            title=self.config.title,
            categories=self.config.categories,
        )

        if output is not None:
            if isinstance(output, Path):
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(md, encoding="utf-8")
                logger.info("Wrote Markdown to %s", output)
            else:
                output.write(md)

        return md
