"""CLI for the landscape generator."""

from __future__ import annotations

import logging
from pathlib import Path

import click

from .cache import Cache
from .github import GitHubClient
from .html_renderer import HTMLRenderer
from .icons import download_favicons
from .md_renderer import MarkdownRenderer
from .parser import parse_landscape_yaml
from .validator import validate_config

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "landscape.yaml"
HTML_OUTPUT_PATH = PROJECT_ROOT / "technology-landscape.html"
MD_OUTPUT_PATH = PROJECT_ROOT / "technology-landscape.md"
ICON_DIR = PROJECT_ROOT / "assets" / "icons"
CACHE_PATH = PROJECT_ROOT / ".landscape-cache.json"

logger = logging.getLogger(__name__)


def setup_logging(verbosity: int) -> None:
    """Configure logging based on verbosity level."""
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@click.group()
@click.version_option(version="0.1.0")
@click.option("-v", "--verbose", count=True, help="Increase verbosity")
@click.pass_context
def main(ctx: click.Context, verbose: int) -> None:
    """Automated technology landscape generator.

    Generates an HTML technology landscape page from structured YAML configuration.
    """
    setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    default=str(CONFIG_PATH),
    help="Path to landscape YAML config",
)
@click.pass_context
def validate(
    ctx: click.Context,
    config: str,
) -> None:
    """Validate landscape config without generating output.

    Checks repo existence, data integrity, and reports warnings/errors.
    """
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"Error: config not found: {config_path}", err=True)
        ctx.exit(1)

    landscape = parse_landscape_yaml(config_path)
    gh_client = GitHubClient(cache=Cache(CACHE_PATH))
    report = validate_config(landscape, github_client=gh_client)

    click.echo(f"\nValidation Report: {landscape.title}")
    click.echo(f"  Categories: {landscape.category_count()}")
    click.echo(f"  Items: {landscape.item_count()}")
    click.echo(f"  ✓ OK: {report.ok}")
    click.echo(f"  ⚠ Warnings: {report.warnings}")
    click.echo(f"  ✗ Errors: {report.errors}")

    if report.warnings > 0:
        click.echo("\nWarnings:")
        for item in report.items:
            if item.warning:
                click.echo(f"  ⚠ {item.category}/{item.name}: {item.warning}")

    if report.errors > 0:
        click.echo("\nErrors:")
        for item in report.items:
            if item.error:
                click.echo(f"  ✗ {item.category}/{item.name}: {item.error}")
        ctx.exit(1)


@main.command()
@click.option(
    "--all",
    is_flag=True,
    help="Clear all cached data",
)
@click.pass_context
def refresh(
    ctx: click.Context,
    all: bool,
) -> None:
    """Refresh cached data or clear all cache."""
    cache = Cache(CACHE_PATH)

    if all:
        cache.clear()
        click.echo("Cache cleared.")
        return

    # Re-fetch all GitHub items from config
    if CONFIG_PATH.exists():
        landscape = parse_landscape_yaml(CONFIG_PATH)
        gh_client = GitHubClient(cache=cache)
        for cat, item in landscape.github_items():
            if item.github_key:
                cache.refresh(item.github_key)
                owner, repo = item.github_key.split("/", 1)
                gh_client.get_repo_info(owner, repo, favicon_url=item.favicon_url)
                click.echo(f"Refreshed: {item.github_key}")

        expired = cache.remove_expired()
        click.echo(f"Removed {expired} expired entries.")
    else:
        click.echo("No config found, cache untouched.")


@main.command()
@click.pass_context
def cache_info(ctx: click.Context) -> None:
    """Show cache statistics."""
    cache = Cache(CACHE_PATH)
    cache_path = CACHE_PATH
    if not cache_path.exists():
        click.echo("Cache not initialized yet.")
        return

    size = cache_path.stat().st_size
    count = len(cache.keys())
    click.echo(f"Cache file: {cache_path}")
    click.echo(f"Size: {size:,} bytes")
    click.echo(f"Entries: {count}")

    # Show top entries by key
    if count > 0:
        click.echo("\nRecent entries:")
        for entry in cache.recent_entries():
            click.echo(
                f"  {entry['key']}: ⭐{entry['stars']} (fetched {entry['fetched_at']})"
            )


@main.command(name="html")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    default=str(CONFIG_PATH),
    help="Path to landscape YAML config",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=str(HTML_OUTPUT_PATH),
    help="Output HTML file path",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force refresh cached data",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--skip-icons",
    is_flag=True,
    help="Skip favicon download",
)
@click.pass_context
def html_command(
    ctx: click.Context,
    config: str,
    output: str,
    force: bool,
    dry_run: bool,
    skip_icons: bool,
) -> None:
    """Generate the technology landscape as a self-contained HTML page.

    Reads YAML config, fetches/refreshes GitHub data, downloads favicons,
    and renders a dark-themed HTML file.
    """
    config_path = Path(config)
    output_path = Path(output)

    if not config_path.exists():
        click.echo(f"Error: config not found: {config_path}", err=True)
        ctx.exit(1)

    # Parse config
    try:
        landscape = parse_landscape_yaml(config_path)
    except Exception as e:
        click.echo(f"Error parsing config: {e}", err=True)
        ctx.exit(1)

    click.echo(f"Landscape: {landscape.title}")
    click.echo(f"  Categories: {landscape.category_count()}")
    click.echo(f"  Items: {landscape.item_count()}")

    # Initialize cache
    cache = Cache(CACHE_PATH)
    if force:
        click.echo("Force refresh: clearing cache...")
        cache.clear()

    # Initialize GitHub client
    gh_client = GitHubClient(cache=cache, dry_run=dry_run)

    # Validate first
    click.echo("\nValidating...")
    report = validate_config(landscape, github_client=gh_client, dry_run=dry_run)

    if report.errors > 0:
        click.echo(f"\n  {report.errors} error(s):", err=True)
        for item in report.items:
            if not item.ok:
                click.echo(f"  ✗ {item.category}/{item.name}: {item.error}", err=True)

    if report.warnings > 0:
        click.echo(f"\n  {report.warnings} warning(s):", err=True)
        for item in report.items:
            if item.warning:
                click.echo(f"  ⚠ {item.category}/{item.name}: {item.warning}", err=True)

    # Download icons
    if not skip_icons:
        click.echo("\nDownloading favicons...")
        try:
            downloaded = download_favicons(
                landscape.all_items(),
                ICON_DIR,
            )
            icon_count = sum(1 for v in downloaded.values() if v)
            click.echo(f"  Downloaded/used {icon_count} favicon(s)")
        except Exception as e:
            click.echo(f"  Warning: icon download failed: {e}", err=True)

    if dry_run:
        click.echo("\nDry run complete. No files written.")
        return

    # Render HTML
    click.echo("\nRendering HTML...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    renderer = HTMLRenderer(landscape)
    renderer.render(report.as_render_data(), output_path)
    click.echo(f"Output: {output_path}")

    # Summary
    click.echo(
        f"\nDone! {report.ok} ok, {report.warnings} warnings, {report.errors} errors"
    )


@main.command(name="markdown")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    default=str(CONFIG_PATH),
    help="Path to landscape YAML config",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=str(MD_OUTPUT_PATH),
    help="Output Markdown file path",
)
@click.pass_context
def markdown_command(
    ctx: click.Context,
    config: str,
    output: str,
) -> None:
    """Generate technology-landscape.md from the YAML config.

    Reads the structured YAML configuration and renders a Markdown document
    that mirrors the hand-written technology-landscape.md, keeping it in sync
    with the source of truth.
    """
    config_path = Path(config)
    output_path = Path(output)

    if not config_path.exists():
        click.echo(f"Error: config not found: {config_path}", err=True)
        ctx.exit(1)

    try:
        landscape = parse_landscape_yaml(config_path)
    except Exception as e:
        click.echo(f"Error parsing config: {e}", err=True)
        ctx.exit(1)

    click.echo(f"Landscape: {landscape.title}")
    click.echo(f"  Categories: {landscape.category_count()}")
    click.echo(f"  Items: {landscape.item_count()}")

    renderer = MarkdownRenderer(landscape)
    renderer.render(output_path)
    click.echo(f"Output: {output_path}")


if __name__ == "__main__":
    main()
