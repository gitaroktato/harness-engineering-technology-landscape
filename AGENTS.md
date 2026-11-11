# AGENTS.md — harness-engineering/landscape

## Quickstart

```bash
cd landscape
uv sync
make html
```

## Using Python

For any python related script or tool you can use only `uv`

Examples for executing packages:

```bash
uvx --with <LIBRARY_NAME> <PACKAGE_NAME> <PARAMETERS>
```

Examples for running a python script:

```bash
uv run /tmp/opencode/<SCRIPT_NAME>
```

```bash
uv run --with python-pptx <SCRIPT_NAME>
```

## Searching within documents

Use `rg` instead of `grep` for searching faster between files.

## Commands

| Task | Command |
| ------ | --------- |
| Generate HTML landscape page | `make html` |
| Validate config (with GitHub API) | `make validate` |
| Force refresh GitHub cache | `make refresh` |
| Show cache status | `make cache-info` |
| Run tests | `uv run pytest` |
| Type-check | `uv run mypy` |
| Lint | `uv run ruff check` |

The Makefile sets `GITHUB_TOKEN` automatically (from the environment, falling back to `gh auth token`) — unauthenticated GitHub API calls are limited to 60 requests/hour, authenticated get 5,000/hour.

## Project Structure

```
landscape/
├── config/landscape.yaml       # Source config (edit this)
├── landscape/technology-landscape.html  # Generated output
├── tools/landscape/            # Python package
│   ├── cli.py                  # CLI entry point: `landscape`
│   ├── models.py               # Pydantic models
│   ├── parser.py               # YAML parsing
│   ├── validator.py            # GitHub validation
│   ├── colors.py               # Shared color palette and star formatter
│   ├── html_renderer.py        # HTML generation (Jinja2)
│   ├── github.py               # GitHub API client (cached)
│   ├── cache.py                # JSON cache (.landscape-cache.json)
│   └── icons.py                # Favicon downloader
├── tests/landscape/            # pytest tests
├── .landscape-cache.json       # GitHub API cache (24h TTL)
├── Makefile                    # Shortcuts
├── pyproject.toml              # uv project config
└── uv.lock                     # Lockfile
```

## Config Format (`config/landscape.yaml`)

```yaml
title: "Technology Landscape"
categories:
  - name: CategoryName
    items:
      - name: ItemName
        repo: owner/repo          # optional, enables GitHub stats + favicon
        url: https://example.com  # optional, used for favicon if no repo
        optional: false           # skip on validation error if true
```

Items without `repo` render without stars/forks.

## Cache

- `.landscape-cache.json` — GitHub API responses cached for 24h (tracked in git; updated by `validate`/`refresh`)
- `make refresh` bypasses the cache

## Testing

```bash
uv run pytest                    # all tests
uv run pytest tests/landscape/test_validator.py  # single file
uv run pytest -k validate        # filter by name
```

## Type-checking

```bash
uv run mypy                        # strict mode (pyproject.toml)
```

## Linting

```bash
uv run ruff check
uv run ruff check --fix            # auto-fix
```

## Env Requirements

- Python 3.11+ (managed by uv)
- `uv` package manager (required)

## Key Files to Know

| File | Purpose |
| ------ | --------- |
| `tools/landscape/cli.py` | All CLI commands (`html`, `validate`, `refresh`, `cache-info`) |
| `tools/landscape/html_renderer.py` | HTML generation (Jinja2 template) |
| `tools/landscape/colors.py` | Shared color palette and star count formatter |
| `tools/landscape/validator.py` | GitHub repo validation + warnings |
| `config/landscape.yaml` | Source of truth for landscape content |
| `.landscape-cache.json` | Local GitHub API cache (auto-managed) |

## Common Gotchas

- **Must run from the repository root** — paths in Makefile/cli.py are relative to it
- **GitHub API rate limits** — set `GITHUB_TOKEN` (60 req/h unauthenticated vs 5,000/h authenticated); the 24h cache helps for repeat runs; use `--force` / `make refresh` to bypass the cache
- **Favicons** downloaded to `assets/icons/` (auto-created)
- **Output dir** `landscape/` is created on first run
- **mypy strict mode** — type annotations required
- **pytest** runs from repo root with `uv run pytest` (discovers `tests/`)

## Historical data for previous agentic sessions

- All session data is available under `.agents/sessions/` folder
- To update the session history use the script `.agents/scripts/export_sessions.sh`
