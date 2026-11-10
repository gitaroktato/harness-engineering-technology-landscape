# Technology Landscape

A living map of the tooling we're keeping an eye on for AI-assisted and spec-driven engineering — coding assistants, orchestration, sandboxes, skills, knowledge bases, token control, observability, and more.

Everything is driven by a single YAML file (`config/landscape.yaml`). When you run the generator it fetches live data from the GitHub API (star counts, descriptions, favicons) and renders the landscape two ways:

- **`technology-landscape.html`** — a self-contained page you can open in any browser or share as-is
- **`technology-landscape.md`** — a Markdown mirror of the same content

So updating the landscape is just: edit the YAML, regenerate. That's it.

## Prerequisites

- Python 3.11+ with [uv](https://github.com/astral-sh/uv) installed

## Setup

```bash
uv sync
```

## Generate the Landscape

```bash
make html
```

This reads `config/landscape.yaml`, enriches each entry from the GitHub API, downloads favicons into `assets/icons/`, and writes out `technology-landscape.html`. Run `make markdown` too if you want the Markdown version.

## Commands

| Command | What it does |
| --------- | ------------- |
| `make html` | Generate the landscape as a self-contained HTML page |
| `make markdown` | Generate the Markdown mirror (`technology-landscape.md`) |
| `make validate` | Check the config, including whether each GitHub repo still exists |
| `make refresh` | Force-refresh the GitHub cache and regenerate |
| `make cache-info` | Show what's in the cache right now |

You can also run any of these directly with `uv run landscape <command>`.

## Configuration

Edit `config/landscape.yaml` to add, remove, or tweak entries. Each item supports:

```yaml
categories:
  - name: SDD
    items:
      - name: OpenSpec
        repo: Fission-AI/OpenSpec      # GitHub owner/repo — used for the API lookup
        optional: false                # set true to skip rendering if validation fails
```

Items without a `repo` field still render, they just don't get star counts or a favicon pulled from GitHub (you can point them at a `url` instead).

## Cache

GitHub API responses are cached in `.landscape-cache.json` for 24 hours so you're not hammering the API on every run. Use `make refresh` to bypass it.
