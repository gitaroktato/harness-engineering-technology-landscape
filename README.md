# Technology Landscape

The project includes an automated tool to generate a [DrawIO](https://draw.io) diagram from structured YAML configuration. The landscape visualizes the technology stack with GitHub repo stats (stars, descriptions) and is rendered as swimlane diagrams.

## Prerequisites

- Python 3.12+ with [uv](https://github.com/astral-sh/uv) installed

## Setup

```bash
uv sync
```

## Build the Landscape

```bash
make landscape
```

This reads `config/landscape.yaml`, enriches data from GitHub API, downloads favicons, and outputs `landscape/technology-landscape.drawio`.

## Commands

| Command | Description |
|---------|-------------|
| `make landscape` | Generate the landscape diagram |
| `make init` | Convert existing markdown to YAML config |
| `make validate` | Validate config (with GitHub API checks) |
| `make refresh` | Force-refresh GitHub cache and regenerate |
| `make cache-info` | Show cache status |

Or run directly with `uv run landscape <command>`.

## Configuration

Edit `config/landscape.yaml` to add, remove, or modify technology items. Each item supports:

```yaml
categories:
  - name: SDD
    items:
      - name: OpenSpec
        repo: Fission-AI/OpenSpec      # GitHub owner/repo for API lookup
        optional: false                 # Skip rendering on validation failure if true
```

Items without a `repo` field are rendered without GitHub data (favicons from URL, no star counts).

## Cache

GitHub API responses are cached in `.landscape-cache.json` with 24h TTL. Use `make refresh` to bypass the cache.
