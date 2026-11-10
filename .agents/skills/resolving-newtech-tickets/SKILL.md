---
name: resolving-newtech-tickets
description: Use when the user asks to resolve, work on, or add a GitHub issue labeled `newtech` in the harness-engineering repo. Covers adding a new technology (or fixing an existing entry's URL/repo/favicon) to the tech landscape config and regenerating the output. Activates for "resolve #NNN", "add <tool> to the landscape", "fix the <tool> URL", or any mention of the `newtech` label.
---

Resolving a `newtech` ticket means updating the tech landscape: edit `landscape/config/landscape.yaml`, regenerate the HTML output, and commit referencing the issue.

## When to Use This Skill

- The user references an issue labeled `newtech` (e.g. "resolve #157", "work on the newtech ticket for X")
- The user asks to add a new tool/technology to the landscape
- The user asks to fix an existing landscape entry's URL, repo, or favicon

## Workflow

All commands run from the `landscape/` directory (paths are relative to it).

### Step 1: Read the ticket

```bash
gh issue list --label newtech          # find open tickets
gh issue view <N>                      # read one ticket
```

A `newtech` ticket is either an **add** (name + URL/repo of a new tool) or a **fix** (wrong URL, repo, or favicon on an existing entry).

### Step 2: Edit `config/landscape.yaml`

Pick the right category (existing ones: SDD, Coding Assistants, SDLC Templates or Template Management, Orchestration, AST and Code Parsers, Sandboxes, Working with Skills, Knowledge Base, Token Control, Observability) and add the item under `items:`:

```yaml
- name: "ToolName"
  favicon: https://tool.example.com/favicon.ico
  url: https://tool.example.com/
  repo: owner/repo
  description: "One or two sentences on what it does."
```

- `favicon:` — the auto-download from `url` is unreliable, so always set it manually. Grab the favicon URL from the item's own website: fetch its HTML and look for `<link rel="icon" ...>` in the head, or try `https://<domain>/favicon.ico`. Put the absolute URL into the YAML.
- For **fix** tickets, edit only the wrong field(s) of the existing entry; do not reorder or reformat surrounding items.

### Step 3: Validate and regenerate

```bash
uv run landscape validate   # checks repo URLs against the GitHub API (cached 24h)
uv run landscape html       # regenerates technology-landscape.html, downloads favicons to assets/icons/
uv run landscape markdown   # regenerates technology-landscape.md
```

If `validate` reports a wrong repo name, fix it in the YAML and re-run. Use `--force` / `uv run landscape refresh` only if cached GitHub data is stale.

### Step 4: Commit and deliver

Stage the YAML change plus regenerated artifacts (`technology-landscape.html`, `technology-landscape.md`, new files under `assets/icons/`).

Commit message follows conventional style with the issue referenced as `(#N)` — never use `Closes`/`Fixes` keywords:

```
feat: HumanLayer (#157)
fix: Graphify URL (#134)
```

Then follow the repo's GitHub workflow (see `landscape/AGENTS.md`): commit to a feature branch, open `gh pr create --base main`, and stop. Never close the issue — closing is left to the owner after merge.

## Gotchas

- Must run from `landscape/` — Makefile/cli paths are relative to it.
- GitHub API rate limits: the 24h cache (`.landscape-cache.json`) handles this; don't bypass it unnecessarily.
- New favicons land in `assets/icons/` and must be committed alongside the regenerated HTML.
- Description strings go in double quotes in the YAML.
