# AGENTS.md — harness-engineering/landscape

## Quickstart

```bash
cd landscape
uv sync
uv run landscape html
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
| Generate HTML landscape page | `uv run landscape html` |
| Validate config (with GitHub API) | `make validate` / `uv run landscape validate` |
| Force refresh GitHub cache | `make refresh` / `uv run landscape refresh` |
| Show cache status | `make cache-info` / `uv run landscape cache-info` |
| Run tests | `uv run pytest` |
| Type-check | `uv run mypy` |
| Lint | `uv run ruff check` |

Set `GITHUB_TOKEN` before `validate`/`refresh` (e.g. `export GITHUB_TOKEN=$(gh auth token)`) — unauthenticated GitHub API calls are limited to 60 requests/hour, authenticated get 5,000/hour.

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

- `.landscape-cache.json` — GitHub API responses cached for 24h (tracked in git; updated by `validate`/`refresh`, commit it with your changes)
- `landscape html --force` or `uv run landscape refresh` bypasses cache

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

## GitHub Issues

Use `gh` CLI. Check open issues before creating to avoid duplicates:
`gh issue list --state open`

- Create an issue for new work, plans, or bugs:
  `gh issue create --title "GPU power cap plan" --body "$(cat plan.md)" --label enhancement`
- Titles: short outcome phrase, no trailing period (e.g. "GPU power cap plan").
- Labels (apply when it fits; plain to-dos may stay unlabeled):
  bug → `bug`, feature → `enhancement`, docs → `documentation`, lessons/postmortems → `lessons`.
  Add later: `gh issue edit 21 --add-label lessons`
- Plan/investigation issues: Background → Findings → Decisions → Execution Steps → Deliverables → Revert.
- Bug issues: what happened, environment (OS/driver/CUDA/model), repro steps, expected vs actual.
- Read an issue: `gh issue view 21`
- Note progress in a comment: `gh issue comment 21 --body "Applied 165W cap, results pending"`
- Reference the issue in commits as `(#N)`. Do NOT use `Closes`/`Fixes` keywords — they auto-close the issue on merge.
- NEVER close an issue yourself (no `gh issue close`, no closing keywords anywhere). Work is delivered via a merge request: work on the current branch if it is not `main` (do not create a new branch per ticket), then open `gh pr create --base main --title "Short outcome phrase" --body "Work for #N"` and stop. The owner reviews and merges the PR; only after that may the issue be closed, and by the owner — not you.
- Batching: multiple `newtech` tickets are handled on the same branch — one commit per ticket, one PR per batch referencing all issues (`Work for #85, #86`).
- Rejections: label `wontfix`, `duplicate`, or `invalid` and comment why; closing is left to the owner.
- Plan changed mid-work? Update the body: `gh issue edit 21 --body "$(cat updated-plan.md)"`
