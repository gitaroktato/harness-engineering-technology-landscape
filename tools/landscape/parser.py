"""Parser for landscape YAML configuration.

Uses Pydantic BaseModel schemas to validate the raw YAML structure before
converting into the internal dataclass models.  This gives us:

- Clear validation errors on malformed config (field names, types, etc.)
- Automatic coercion (e.g. int ``optional`` → bool)
- A single source-of-truth schema that documents the allowed YAML shape
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator

from .models import LandscapeCategory, LandscapeConfig, LandscapeItem, LandscapeSubGroup

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic input schemas  (validate the raw YAML dict structure)
# ---------------------------------------------------------------------------


class _ItemSchema(BaseModel):
    """Schema for a single landscape item entry in YAML."""

    name: str = "Unknown"
    repo: str | None = None
    url: str | None = None
    description: str | None = None
    icon: str | None = None
    favicon: str | None = None
    optional: bool = False


class _SubGroupSchema(BaseModel):
    """Schema for a named sub-group inside a category."""

    name: str = "Group"
    items: list[_ItemSchema] = Field(default_factory=list)


class _CategorySchema(BaseModel):
    """Schema for a category entry in YAML."""

    name: str = "Uncategorized"
    subtitle: str | None = None
    items: list[_ItemSchema] = Field(default_factory=list)
    groups: list[_SubGroupSchema] = Field(default_factory=list)


class _LandscapeSchema(BaseModel):
    """Schema for the top-level landscape YAML document."""

    title: str = "Technology Landscape"
    categories: list[_CategorySchema] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _must_be_mapping(cls, v: Any) -> Any:
        """Ensure the YAML root is a mapping, not a sequence or scalar."""
        if not isinstance(v, dict):
            raise ValueError("YAML root must be a mapping")
        return v


# ---------------------------------------------------------------------------
# Conversion helpers:  Pydantic schema → internal dataclass models
# ---------------------------------------------------------------------------


def _item_from_schema(schema: _ItemSchema) -> LandscapeItem:
    return LandscapeItem(
        name=schema.name,
        repo=schema.repo,
        url=schema.url,
        description=schema.description,
        icon=schema.icon,
        favicon=schema.favicon,
        optional=schema.optional,
    )


def _subgroup_from_schema(schema: _SubGroupSchema) -> LandscapeSubGroup:
    return LandscapeSubGroup(
        name=schema.name,
        items=[_item_from_schema(i) for i in schema.items],
    )


def _category_from_schema(schema: _CategorySchema) -> LandscapeCategory:
    cat = LandscapeCategory(
        name=schema.name,
        subtitle=schema.subtitle,
        items=[_item_from_schema(i) for i in schema.items],
        groups=[_subgroup_from_schema(g) for g in schema.groups],
    )
    return cat


def _config_from_schema(schema: _LandscapeSchema) -> LandscapeConfig:
    return LandscapeConfig(
        title=schema.title,
        categories=[_category_from_schema(c) for c in schema.categories],
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_landscape_yaml(path: Path) -> LandscapeConfig:
    """Parse a landscape YAML configuration file.

    A category may define either a flat ``items`` list OR a ``groups`` list
    of named sub-groups (each containing their own ``items``).  Both keys
    can coexist, though the convention is to use one or the other.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed LandscapeConfig object.

    Raises:
        yaml.YAMLError: If the YAML is malformed.
        ValueError: If required fields are missing or the root is not a mapping.
        pydantic.ValidationError: If the YAML structure does not match the schema.
    """
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    schema = _LandscapeSchema.model_validate(data)
    config = _config_from_schema(schema)

    logger.info(
        "Parsed landscape: %d categories, %d items",
        config.category_count(),
        config.item_count(),
    )
    return config


def dump_landscape_yaml(config: LandscapeConfig) -> str:
    """Dump a LandscapeConfig to YAML string.

    Useful for the init command to convert MD -> YAML.

    Args:
        config: The landscape configuration to serialize.

    Returns:
        YAML-formatted string.
    """
    categories: list[dict[str, Any]] = []

    for cat in config.categories:
        cat_dict: dict[str, Any] = {"name": cat.name}
        if cat.subtitle:
            cat_dict["subtitle"] = cat.subtitle

        flat_items: list[dict[str, Any]] = []
        for item in cat.items:
            flat_items.append(_item_to_dict(item))
        if flat_items:
            cat_dict["items"] = flat_items

        if cat.groups:
            groups_list: list[dict[str, Any]] = []
            for group in cat.groups:
                group_dict: dict[str, Any] = {
                    "name": group.name,
                    "items": [_item_to_dict(i) for i in group.items],
                }
                groups_list.append(group_dict)
            cat_dict["groups"] = groups_list

        # Preserve empty items key when no items and no groups (matches prior behaviour)
        if "items" not in cat_dict and not cat.groups:
            cat_dict["items"] = []

        categories.append(cat_dict)

    data: dict[str, Any] = {
        "title": config.title,
        "categories": categories,
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _item_to_dict(item: LandscapeItem) -> dict[str, Any]:
    """Serialize a LandscapeItem to a plain dict for YAML dumping."""
    d: dict[str, Any] = {"name": item.name}
    if item.repo:
        d["repo"] = item.repo
    if item.url:
        d["url"] = item.url
    if item.description:
        d["description"] = item.description
    if item.icon:
        d["icon"] = item.icon
    if item.favicon:
        d["favicon"] = item.favicon
    if item.optional:
        d["optional"] = True
    return d
