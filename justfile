set shell := ["bash", "-cu"]

default: all

# Run formatter, linter, tests
all: fmt lint test

# Install / sync dependencies
sync:
    uv sync

# Format with ruff
fmt:
    uv run ruff format src tests

# Lint with ruff
lint:
    uv run ruff check src tests

# Run the unit test suite with coverage (default — skips integration)
test *ARGS:
    uv run pytest {{ARGS}}

# Run a single test path
test-one PATH:
    uv run pytest -x -vv --no-cov {{PATH}}

# Run integration tests only (real git / subprocess / filesystem)
test-integration *ARGS:
    uv run pytest -m integration --no-cov -ra {{ARGS}}

# Run BOTH unit and integration suites
test-all *ARGS:
    uv run pytest -m "" {{ARGS}}

# Run the CLI in dev
run *ARGS:
    uv run identikit {{ARGS}}

# Clean build artifacts
clean:
    rm -rf dist build .pytest_cache .ruff_cache .coverage htmlcov
