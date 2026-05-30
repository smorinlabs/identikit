.PHONY: check all sync fmt lint test run clean

check:
	@command -v uv >/dev/null || { echo "missing: uv (https://docs.astral.sh/uv/)"; exit 1; }
	@command -v just >/dev/null || { echo "missing: just (https://github.com/casey/just)"; exit 1; }
	@echo "ok: uv $$(uv --version | awk '{print $$2}'), just $$(just --version | awk '{print $$2}')"

all sync fmt lint test run clean:
	@just $@
