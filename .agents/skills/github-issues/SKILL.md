---
name: github-issues
description: Working with GitHub issues and PRs in this repo via the gh CLI. Use when creating, viewing, commenting on, or labeling issues, planning work, opening a PR, or referencing an issue from a commit.
---

# GitHub Issues

Use the `gh` CLI. Check open issues before creating to avoid duplicates:
`gh issue list --state open`

## Conventions

- Create an issue for new work, plans, or bugs:
  `gh issue create --title "GPU power cap plan" --body "$(cat plan.md)" --label enhancement`
- Titles: short outcome phrase, no trailing period (e.g. "GPU power cap plan").
- Labels (apply when it fits; plain to-dos may stay unlabeled):
  bug → `bug`, feature → `enhancement`, docs → `documentation`, lessons/postmortems → `lessons`.
  Add later: `gh issue edit 21 --add-label lessons`
- Reference the issue in commits as `(#N)`. Do NOT use `Closes`/`Fixes` keywords — they auto-close the issue on merge.

## Issue templates

- Plan/investigation issues: Background → Findings → Decisions → Execution Steps → Deliverables → Revert.
- Bug issues: what happened, environment (OS/driver/CUDA/model), repro steps, expected vs actual.

## Day-to-day

- Read an issue: `gh issue view 21`
- Note progress in a comment: `gh issue comment 21 --body "Applied 165W cap, results pending"`
- Plan changed mid-work? Update the body: `gh issue edit 21 --body "$(cat updated-plan.md)"`

## Delivery and closing

- NEVER close an issue yourself (no `gh issue close`, no closing keywords anywhere). Work is delivered via a merge request: commit to a feature branch, then open `gh pr create --base main --title "Short outcome phrase" --body "Work for #N"` and stop. The owner reviews and merges the PR; only after that may the issue be closed, and by the owner — not you.
- Rejections: label `wontfix`, `duplicate`, or `invalid` and comment why; closing is left to the owner.
