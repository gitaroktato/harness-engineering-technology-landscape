"""Shared color palette and formatting utilities for landscape renderers."""

from __future__ import annotations


# Color palette for categories (alternating light backgrounds with matching strokes).
# Each tuple is (fill_color, stroke_color).
CATEGORY_PALETTE = [
    ("#dae8fc", "#6c8ebf"),  # blue
    ("#d5e8d4", "#82b366"),  # green
    ("#ffe6cc", "#d6b656"),  # orange
    ("#e1d5e7", "#9673a6"),  # purple
    ("#fff2cc", "#d6b656"),  # yellow
    ("#fce4ec", "#e91e63"),  # pink
]


def _fmt_stars(stars: int | None) -> str:
    """Format star count for display (e.g. 62.9k)."""
    if stars is None:
        return "?"
    if stars >= 1000:
        return f"{stars / 1000:.1f}k"
    return str(stars)
