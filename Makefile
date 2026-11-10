.PHONY: init validate refresh cache-info help

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
	uv run landscape validate

refresh:
	uv run landscape refresh

cache-info:
	uv run landscape cache-info
