---
name: resolving-newtech-tickets
description: Use when the user asks to resolve, work on, or add a GitHub issue labeled `newtech` in this tech landscape repo. Covers adding a new technology (or fixing an existing entry's URL/repo/favicon) to the tech landscape config and regenerating the output. Activates for "resolve #NNN", "add <tool> to the landscape", "fix the <tool> URL", or any mention of the `newtech` label.
---

Resolving a `newtech` ticket means updating the tech landscape: edit `config/landscape.yaml`, regenerate the HTML/Markdown output, and commit referencing the issue. Tickets are processed in **batches**: many tickets per branch, one validate + regeneration cycle at the end.

## When to Use This Skill

- The user references an issue labeled `newtech` (e.g. "resolve #157", "work on the newtech ticket for X")
- The user asks to add a new tool/technology to the landscape
- The user asks to fix an existing landscape entry's URL, repo, or favicon

## Workflow

All commands run from the repository root (paths below are relative to it). Work on the current branch if it is not `main` — do not create a new branch per ticket or batch.

### Step 1: Pick the batch

```bash
gh issue list --label newtech          # find open tickets
gh issue view <N>                      # read one ticket
```

Process the tickets the user named, or all open ones if told to clear the backlog. A `newtech` ticket is either an **add** (name + URL/repo of a new tool) or a **fix** (wrong URL, repo, or favicon on an existing entry).

### Step 2: Per ticket — research and edit `config/landscape.yaml`

1. Research with the authenticated GitHub CLI — never raw `curl` to api.github.com (it hits unauthenticated rate limits):

   ```bash
   gh api repos/<owner>/<repo> --jq '{desc: .description, stars: .stargazers_count, homepage: .homepage}'
   ```

2. Favicon: the auto-download from `url` is unreliable, so always set it manually. Fetch the item's own website HTML and look for `<link rel="icon" ...>` in the head, or try `https://<domain>/favicon.ico`. Put the absolute URL into the YAML.
3. **Confirm category & group** (add tickets only — skip for fixes): before editing the YAML, ask the user which category (and sub-group, if the category has `groups:`) the tool belongs to.

   - Lead with a 1–2 sentence factual summary of what you found during research (repo description, homepage, key capabilities) so the user sees *why* you're recommending a placement.
   - If you are confident in a single placement, present just that one option and ask for confirmation (e.g. "X is a terminal-based multi-agent orchestrator with task queues → **Orchestration**. Confirm?").
   - If you are unsure, offer exactly 3 alternatives (category + group), each preceded by the same factual summary or a targeted subset of it explaining why that bucket fits.
   - Do not proceed to the YAML edit until the user confirms. Batch multiple confirmations into one message when processing several add tickets.
4. Add the item under the confirmed category's `items:` (or a group's `items:`). Existing categories: SDD, Coding Assistants, SDLC Templates or Template Management, Orchestration, AST and Code Parsers, Sandboxes, Working with Skills, Knowledge Base, Token Control, Observability:

   ```yaml
   - name: "ToolName"
     favicon: https://tool.example.com/favicon.ico
     url: https://tool.example.com/
     repo: owner/repo
     description: "One or two sentences on what it does."
   ```

   - For **fix** tickets, edit only the wrong field(s) of the existing entry; do not reorder or reformat surrounding items.
   - Description strings go in double quotes.
5. Commit per ticket, conventional style with the issue referenced as `(#N)` — never use `Closes`/`Fixes` keywords:

   ```
   feat: HumanLayer (#157)
   fix: Graphify URL (#134)
   ```

Do NOT validate or regenerate output per ticket — do it once at the end (Step 3).

### Step 3: At batch end — validate and regenerate (once)

```bash
GITHUB_TOKEN=$(gh auth token) uv run landscape validate   # checks repo URLs against the GitHub API (cached 24h)
uv run landscape html       # regenerates technology-landscape.html, downloads favicons to assets/icons/
uv run landscape markdown   # regenerates technology-landscape.md
```

- Always set `GITHUB_TOKEN` for `validate` — 60 req/h unauthenticated vs 5,000/h authenticated.
- If `validate` reports a wrong repo name, fix it in the YAML and re-run. Use `--force` / `uv run landscape refresh` only if cached GitHub data is stale.
- If `validate` is still rate-limited, do not block the batch: keep the YAML commits and note in the PR that validation is pending.
- Commit the regenerated artifacts (`technology-landscape.html`, `technology-landscape.md`, new files under `assets/icons/`, plus any updated `.landscape-cache.json`) as a single final commit.

### Step 4: Deliver

Push the current branch and open one PR for the whole batch (update the existing PR if the branch already has one):

```bash
gh pr create --base main --title "Short outcome phrase" --body "Work for #85, #86, #87"
```

Delivery and closing: never close the issues; closing is left to the owner after merge.

## Gotchas

- Must run from the repository root — Makefile/cli paths are relative to it.
- GitHub API rate limits: set `GITHUB_TOKEN` for authenticated calls; the 24h cache (`.landscape-cache.json`) handles repeat runs. Don't bypass the cache unnecessarily.
- Regenerate output once per batch, not per ticket — repeated regenerations just overwrite each other and burn API quota.
- New favicons land in `assets/icons/` and must be committed alongside the regenerated HTML.
