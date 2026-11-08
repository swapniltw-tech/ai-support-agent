.DEFAULT_GOAL := help

# Load .env for local runs only. Code itself reads the real environment;
# in CI/Kubernetes these variables come from the platform, not a file.
UV_RUN := uv run
ENV_RUN := uv run --env-file .env

.PHONY: help install run test lint format check clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

install: ## Sync the virtualenv with pyproject.toml / uv.lock
	uv sync

run: ## Run the app locally, loading .env
	$(ENV_RUN) policypal

test: ## Run unit tests (no .env, no live API)
	$(UV_RUN) pytest

lint: ## Lint with ruff (no changes)
	$(UV_RUN) ruff check .
	$(UV_RUN) ruff format --check .

format: ## Auto-fix lint issues and format code
	$(UV_RUN) ruff check --fix .
	$(UV_RUN) ruff format .

check: lint test ## Everything to run before a commit

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .ruff_cache build dist
	find . -type d -name __pycache__ -not -path './.venv/*' -prune -exec rm -rf {} +
