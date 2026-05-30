# identikit

**Rewrite a live template repo's identity into a new project — one-shot, in-place, config-driven.**

`identikit` answers one question — *"how do I turn this template repo into my own project?"* — without
tokenizing the template. A blueprint repo stays a real, runnable, CI-green project (no `{{tokens}}`); its
own identity values (package name, repo name, CLI command, owner, author) are the "from" side of a
deterministic rewrite. Point `identikit` at a per-repo config and it stamps your project's identity in
place: text replacements, file/dir renames, removals, lockfile regeneration, and optional feature
selection via [`toggle`](https://github.com/smorin/toggle).

## Install / run

```bash
# Run without installing (recommended)
uvx identikit --help

# From a clone, no install / no `uv sync` needed
uv run identikit --help
```

## Commands

```
identikit discover -c identikit.toml [-o OUT]   # author: scan repo → draft config
identikit init [-c identikit.toml]              # creator: rebrand in place (one-shot)
               [--answers FILE] [--dry-run] [--force] [--allow-dirty] [--yes] [--no-lockfile]
identikit doctor [-c identikit.toml]            # audit: fail if any "from" value leaks
identikit prune [-c identikit.toml]             # remove the identikit footprint post-init
```

### Two-phase workflow

1. **Template author** runs `identikit discover` once: it scans the repo for the seeded identity values
   and emits a draft `identikit.toml` (identity fields + replace/rename/remove/regenerate manifest).
   Review, curate, commit. The config travels with every instantiation.
2. **Project creator** runs `identikit init`: preflight (git clean, not already initialized, `.git`
   present) → collect answers (interactive with git-derived defaults, or `--answers` for headless/CI) →
   preview plan → apply `remove → replace → rename → regenerate` → activate features via `toggle` →
   write the one-shot marker.

`init` is **one-shot** (the marker refuses a second run) and **safe** (requires a clean git tree — git is
the undo button). It handles the five instantiation modes (template button, `gh --template`,
clone-reinit, fork, ZIP); a fork's origin can't misdirect the rewrite because the "from" identity is
fixed in config, never derived from the instance.

## Config (`identikit.toml`)

```toml
[identity.package_name]
value    = "py_launch_blueprint"     # the "from" value in THIS repo (invariant)
validate = "python_identifier"
prompt   = "Python package name"
derive   = "repo_name|snake"         # default-derivation rule for the "to" value

[identity.repo_name]
value    = "py-launch-blueprint"
validate = "repo_name"
prompt   = "repo name"
derive   = "origin.repo"

[[replace]]
field = "package_name"
files = ["pyproject.toml", "src/py_launch_blueprint/__init__.py"]
mode  = "text"                       # text | structured

[[rename]]
from = "py_launch_blueprint"
to   = "{package_name}"

[[remove]]
path   = ".github/workflows/blueprint-guard.yml"
reason = "guard CI is template-only"

[[regenerate]]
path    = "uv.lock"
command = ["uv", "lock"]

[features.db]                        # optional, activated via `toggle` (graceful if absent)
variants = ["sqlite", "postgres"]
prompt   = "database driver?"
default  = "sqlite"

[guard]
skip_if_origin = ["smorinlabs/py-launch-blueprint"]

[prune]
paths = ["identikit", "identikit.toml"]
```

See [`identikit-spec.md`](./identikit-spec.md) for the full design of record (decisions D0–D4, the
delivery architecture, and the post-init split).

## Development

```bash
make check        # verify uv + just are present
just all          # fmt + lint + unit tests (the fast inner loop)
just test-all     # unit + integration (guard.sh subprocess tests)
```

Coverage gate is 85% (enforced in `pyproject.toml`); current coverage ~91%.

## License

MIT (see `LICENSE`).
