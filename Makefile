.PHONY: init validate refresh cache-info help

# Use GITHUB_TOKEN from the environment if set, otherwise fall back to `gh auth token`
GITHUB_TOKEN ?= $(shell command -v gh >/dev/null 2>&1 && gh auth token 2>/dev/null)

help:
	@echo "Available targets:"
	@echo "  html        Generate lansdcape in HTML format"
	@echo "  markdown    Generate landscape markdown description"
	@echo "  validate    Validate landscape configuration (with GitHub API checks)"
	@echo "  refresh     Force-refresh GitHub API cache"
	@echo "  cache-info  Show cache status"

html:
	uv run landscape html

markdown:
	uv run landscape markdown

validate:
	GITHUB_TOKEN="$(GITHUB_TOKEN)" uv run landscape validate

refresh:
	GITHUB_TOKEN="$(GITHUB_TOKEN)" uv run landscape refresh

cache-info:
	uv run landscape cache-info
