.PHONY: setup kernels check lint fmt test api clean

setup:
	uv sync --all-extras
	uv run pre-commit install

kernels:
	uv run python scripts/fetch_kernels.py

check: lint test

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src

fmt:
	uv run ruff format .
	uv run ruff check --fix .

test:
	uv run pytest

api:
	uv run uvicorn lunarwindow.api.main:app --reload --port 8000

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
