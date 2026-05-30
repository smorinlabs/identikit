# identikit — Projects

Status legend: `[?]` idea · `[ ]` scoped · `[~]` in progress · `[x]` done · `[-]` dropped · `[>]` superseded

## [x] Project P01: identikit core v0.1.0 (v0.1.0)
**Goal**: A working `identikit` CLI that rewrites a live template repo's identity into a new
project — one-shot, in-place, config-driven — per `identikit-spec.md`. Field-agnostic identity,
graceful `toggle` feature gating, and the five instantiation modes handled.

**Out of scope (this version)**
- Terraform module + SaaS-trust walkthrough (post-init; D3 — designed out of core)
- YAML/JSON structured rewriters (only TOML is structured today; others use text)

### Tests & Tasks
- [x] [P01-T01] Scaffold package (pyproject `uv_build` + `src/identikit/`, just/make, pytest)
- [x] [P01-T02] `common.py` — config model, validators, origin parse, `load_config`
- [x] [P01-TS02] Tests: validators, origin parse across the 5 modes, config round-trip
- [x] [P01-T03] `engine.py` — `build_plan` + `apply` (remove → replace → rename → regenerate)
- [x] [P01-TS03] Tests: plan resolution, text replace longest-first, rename templating, regenerate DI
- [x] [P01-T04] `discover.py` — scan repo for identity values, emit draft `identikit.toml`
- [x] [P01-TS04] Tests: scan counts, mode heuristic, rename/regenerate detection, round-trip
- [x] [P01-T05] `features.py` — `toggle` integration (graceful skip when absent)
- [x] [P01-TS05] Tests: builds toggle invocations, graceful skip, unknown variant/group
- [x] [P01-T06] `doctor.py` — no-leak audit
- [x] [P01-TS06] Tests: detects leaks, passes on clean tree, excludes config/bootstrap
- [x] [P01-T07] `cli.py` — `discover` / `init` / `doctor` / `prune` (typer); `defaults`/`preflight`/`marker`/`gitctx`
- [x] [P01-TS07] Tests: preflight, dry-run, headless + interactive, marker, version
- [x] [P01-TS08] Integration: one fixture per instantiation mode (template/gh/clone/fork/zip)
- [x] [P01-T08] `guard.sh` — warn/block modes, config-driven skip (+ subprocess tests)
- [x] [P01-T09] `rewriters.py` — structured tomlkit rewriter (comment-preserving), wired into engine
- [x] [P01-T10] `examples/py-launch-blueprint/identikit.toml` — real dogfood config (+ coherence test)
- [x] [P01-T11] CI + OIDC trusted publishing + release-please (mirrors py-launch-blueprint)
- [x] Regression Test Status: `just all` green — 92 tests, ~92% coverage; actionlint + yamllint clean

## [ ] Project P02: Publish identikit 0.1.0 to PyPI (v0.1.0)
**Goal**: First public release via the new pipeline.
### Tests & Tasks
- [ ] [P02-T01] Configure PyPI trusted publisher (owner=smorinlabs, repo=identikit, workflow=publish.yml, env=pypi)
- [ ] [P02-T02] Create the `pypi` GitHub environment
- [ ] [P02-T03] Set release-please auth (App secrets or RELEASE_PLEASE_APP_TOKEN)
- [ ] [P02-T04] Merge release-please PR → tag → verify `uvx identikit --version`

### Automated Verification
- `make check` passes (uv + just present)
- `just all` (fmt + lint + test) green, coverage ≥ 85%
- `uv run identikit --version` prints the version
