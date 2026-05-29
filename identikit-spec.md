# identikit — Design Specification

**A standalone tool that rewrites a live template repo's identity into a new project — one-shot, in-place, config-driven.**

Status: **design of record, pre-implementation.** This document captures the analysis, the
design space, and the decisions locked so far. No engine code exists yet.

---

## 1. Summary

When a developer creates a repo from a GitHub *template*, the new project still carries the
template's identity — package name, repo name, CLI command, owner, author, email, URLs.
`identikit` guides (or headlessly drives) the developer through **deterministically rewriting that
identity into their own project's values**, then stops. It is a one-time scaffolding step, not a
living link back to the template.

The design is distilled from the `py-launch-blueprint` `init/` self-setup system: that system's
**identity-agnostic rebrand engine, extracted as a reusable standalone tool** driven by a per-repo
config, with the template-specific and stack-specific parts removed from the core.

Key property preserved from the source system: the template repo stays a **real, runnable,
CI-green project** (no `{{tokens}}`). Its own live identity values are the "from" side of the
rewrite. The repo is simultaneously the demo and the template.

---

## 2. Background — the source system

`py-launch-blueprint/init/` (~3,500 lines) is a self-rebrand system with two distinct concerns
bundled together:

| Concern | Files | Nature |
|---|---|---|
| **A. Rebrand engine** | `_engine.py`, `common.py`, `discover.py`, `manifest.toml`, `init.py`, `_rewriters.py`, doctor *migration* checks | mechanism + data — **identity-agnostic by design** |
| **B. Service wiring** | `post_init.py` (804 lines), `setup-*.sh`, doctor *environment* checks, `guard.sh` | opinionated to a specific stack (uv + release-please + OIDC + gh) |

What the source system already gets right (and `identikit` keeps):
- The engine is **config-driven**: `manifest.toml` is the single source of truth for *what* gets
  rewritten; the engine is a pure mechanism (remove → replace → rename → regenerate).
- A `discover` script scans the repo for identity occurrences and emits a draft manifest.
- A strict **one-shot marker** gates re-runs; a clean git tree is required (git is the undo button).
- Five **instantiation modes** are pinned as a regression contract (see §8).

What made it *feel* repo-specific (and what `identikit` fixes):
- The "from" identity (`BLUEPRINT_IDENTITY`) is **hardcoded in Python** (`common.py`), even though
  the manifest it drives is data. → Move it into config.
- `Answers` is a `@dataclass(frozen=True)` with six **named** fields. → Make identity a
  field-agnostic `dict[str, str]`. **This is the binding refactor.**
- The PyPI/release-please **service wiring and the `just`-eager-eval guard are baked into the
  core.** → Pull them out as opt-in concerns / plugins.

---

## 3. Scope

### In scope
- A one-shot, in-place, config-driven identity rewrite of an instantiated template repo.
- A `discover` command for template authors to generate the per-repo config.
- A `doctor` command auditing that no "from" identity values leak post-rebrand.
- Field-agnostic identity (works for any set of identity fields, not a fixed six).

### Out of scope (deliberately)
- **Template updates / propagation.** `identikit` is one-shot: the template→project relationship
  ends at creation. No re-applying upstream template changes, no merge/3-way, no bidirectional
  patch flow. (This is what ruled out copier and the "identity-map" design — see §4.)
- **Service wiring in the core.** Publishing, Codecov, ReadTheDocs, secrets, environments are
  handled outside the rebrand core (see §9).
- **Tokenizing the template.** The template must remain runnable and CI-green.

---

## 4. Locked design decisions

| # | Decision | Rationale |
|---|---|---|
| **D0. One-shot** | The template→project relationship ends at creation. | User requirement. Eliminates the hardest problem (update/merge), and with it copier and the identity-map design. The marker is a pure gate + record, never a live map. |
| **D1. Delivery = published `uvx` engine (Design B)** | One canonical engine on PyPI, semver-pinned; each repo ships only `identikit.toml` + a ~5-line shim. | Single source of truth; pins via `identikit==X`; matches the reserved PyPI name and the `uvx`-run idiom. First run needs network (acceptable — instantiation happens online). Alternatives A/C considered — see §6. |
| **D2a. "From" identity = explicit config values** | Each old value lives in `identikit.toml` `[identity.*].value`; invariant across all instantiation modes. | A fork's `origin` *misreports* the old owner; clone-reinit and ZIP have no origin at all. The "from" side must not be derived from the instance's git state or it would fail to replace values (e.g. leave `smorinlabs` in a fork). |
| **D2b. "To" defaults = conditional on git state** | Pre-filled prompt defaults derive from `origin` + `git config`, guarded. | Best UX for the common template-button case; safe on the edge modes. Guards: skip when `origin` matches the template (fork), and when the derived "to" repo name would collide with the "from" repo name; fall back to `git config` / empty when origin is absent. Always overridable; `--config` bypasses entirely. |
| **D3. Post-init split out of core** | Declarative GitHub config → Terraform/OpenTofu module shipped in the template. SaaS trust → a thin optional walkthrough. Core does rebrand only. | Lifecycle mismatch: rebrand is one-shot + destructive; service config is declarative + idempotent. ~80% of the source `post_init.py` is designed out. See §9. |

---

## 5. Shared model

These elements are the same regardless of delivery mechanism.

### 5.1 Two actors, two phases

```
  TEMPLATE AUTHOR  ── once, in the template repo ────────────────────────┐
  ┌──────────────────────────────────────────────────────────────────┐  │
  │  live template repo  (runnable · CI-green · NO {{tokens}})         │  │
  │        │  identikit discover     (scan repo for identity values)   │  │
  │        ▼                                                           │  │
  │  draft identikit.toml  ──▶  human review/curate  ──▶  commit       │  │
  │     [identity] (the "from" values + field metadata)                │  │
  │     [[replace]] [[rename]] [[remove]] [[regenerate]] [guard]       │  │
  └────────┼───────────────────────────────────────────────────────── ┘  │
           │  config travels with every clone / template instantiation     │
           ▼                                                               ◀┘
  PROJECT CREATOR  ── once per new project ──────────────────────────────┐
  ┌──────────────────────────────────────────────────────────────────┐  │
  │  instantiated repo  (still carries template identity)              │  │
  │        │  identikit init        (answers = the new identity)       │  │
  │        ▼                                                           │  │
  │  rebranded repo  +  marker (record: identity used, version, date)  │  │
  │        │  one-shot: marker refuses a second run (unless --force)   │  │
  │  identikit doctor   (audit: zero "from" values leak)              │  │
  └──────────────────────────────────────────────────────────────────┘  │
                                                                          ◀┘
```

`discover` is the role-flip from the source system: there it was a throwaway that deleted itself;
here it is the **author's onboarding command** — what makes a *new* template adoptable without
hand-writing a manifest.

### 5.2 The one config file (`identikit.toml`)

Merges the two sources the source system split awkwardly — hardcoded identity + manifest.

```toml
# identikit.toml — generated by `identikit discover`, curated by the author.

# ── identity: the fields to rewrite. `value` = the "from" string in THIS repo (D2a).
[identity.package_name]
value    = "py_launch_blueprint"
validate = "python_identifier"
prompt   = "Python package name (snake_case)"
[identity.repo_name]
value    = "py-launch-blueprint"
validate = "repo_name"
prompt   = "repo name (kebab-case)"
derive   = ""                         # optional default-derivation rule for the "to" value
# … owner, command_name, author, email …

# ── manifest: where each field is rewritten, and how.
[[replace]]
field = "package_name"
files = ["pyproject.toml", "src/py_launch_blueprint/__init__.py"]
mode  = "structured"                  # structured (toml/targeted) | text (prose)

[[rename]]
from = "py_launch_blueprint"
to   = "{package_name}"

[[remove]]
path   = ".github/workflows/blueprint-guard.yml"
reason = "guard CI is template-only"

[[regenerate]]
path    = "uv.lock"
command = ["uv", "lock"]

# ── guard + prune: build-tool-agnostic config (wiring is a plugin, §5.4)
[guard]
skip_if_origin = ["smorinlabs/py-launch-blueprint"]
block          = ["build", "publish"]
[prune]
paths = ["identikit/", ".github/workflows/blueprint-guard.yml"]
```

### 5.3 The engine pipeline (`init`-time)

```
 identikit init
   │
   ├─▶ preflight     .git present? · marker absent (or --force)? · tree clean
   │                 (or --allow-dirty)? · required tools present?
   │                 └─ handles the 5 instantiation modes (§8)
   ├─▶ answers       interactive prompts (from [identity])  │  --config answers.toml
   │                 "to" defaults derived from git, guarded (D2b) · each value validated
   ├─▶ plan          resolve manifest × answers → concrete edit/rename/remove list
   ├─▶ preview       print plan · --dry-run stops here · else confirm
   ├─▶ apply         remove → replace → rename → regenerate
   │                 (any failure → tell user: `git checkout . && git clean -fd`)
   ├─▶ marker        write record (identity used · engine version · date)
   └─▶ lockfiles     uv lock · bun install (regenerate, never hand-edit)
```

Order **remove → replace → rename → regenerate** is load-bearing: remove shrinks the working set;
replace runs while paths still match the manifest's `files` lists; rename runs last so nothing sees
a path under its new name; regenerate (lockfiles) runs after the new name exists.

### 5.4 Core vs plugin boundary

```
 ┌───────────────────────── identikit CORE (stack-agnostic) ─────────────────────┐
 │  discover · build-plan · apply(remove/replace/rename/regenerate) · doctor      │
 │  identity = dict[field → value]      (field-agnostic; knows no toolchain)      │
 └───────────────▲──────────────────────────────────────────────▲───────────────┘
                 │ opt-in                                         │ opt-in
        ┌────────┴─────────┐                            ┌─────────┴──────────┐
        │ STACK plugin     │                            │ GUARD plugin       │
        │ (see §9 — mostly │                            │ warn/block wiring  │
        │  Terraform now)  │                            │ for just/make/npm  │
        └──────────────────┘                            └────────────────────┘
```

### 5.5 Field-agnostic identity (the binding refactor)

The source system's `Answers` is a frozen dataclass with six named fields, which hardwires the
field set into Python. `identikit` represents identity as `dict[str, str]` keyed by the
`[identity.*]` names from config. Everything else (rename templating via `{field}`, the
replacement map, validators) already iterates generically — so this one change is ~90% of "make it
reusable across stacks."

---

## 6. Delivery architecture (Design B) and the alternatives considered

**Chosen — Design B: externalized `uvx` tool + config-only repos.**

```
              PyPI / git  (ONE engine, semver-pinned)
              ┌──────────────────────────┐
              │     identikit  @ v1.2.0   │
              └─────────────┬────────────┘
                            │  uvx --from identikit==1.2.0 identikit init
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
     repo A              repo B              repo C
     identikit.toml      identikit.toml      identikit.toml
     + shim + guard      + shim + guard      + shim + guard
     (config only — NO engine code vendored)
```

Thin shim that preserves the bare-clone / `just`-friendly UX:

```sh
# identikit/run.sh
exec uvx --from "identikit==1.2.0" identikit "$@"
```

**Alternatives considered and rejected:**

- **Design A — vendored engine source per repo.** Self-contained, offline, zero infra; but the
  engine is copy-pasted into every template → drift, and fixes must be re-copied by hand. Fallback
  only if a published package is not maintained.
- **Design C — vendored single-file `.pyz`, pinned + CI drift-checked.** Offline + byte-reproducible
  with a verified single source; but most moving parts (build the `.pyz`, vendor it, maintain the
  drift check). Reserve as a later hardening option **only if** offline / air-gapped instantiation
  ever becomes a requirement.

| Property | A. Vendored | **B. uvx tool** | C. Hybrid |
|---|:--:|:--:|:--:|
| Bare clone / offline | ✅ | ⚠ first run online | ✅ |
| Single source of truth | ❌ drift | ✅ by construction | ✅ verified by CI |
| Version pinning | manual | ✅ `==X` | ✅ hash + vX |
| Prune in one step | ✅ | ✅ (config + shim) | ✅ |
| New external infra | none | publish package | publish + build `.pyz` + CI check |
| Complexity | low | medium | medium-high |

---

## 7. Identity resolution across instantiation modes

There are two identities. The "from" side (D2a) is invariant; the "to" defaults (D2b) are
conditional on git state.

```
 mode                     │ "FROM" (what to replace)    │ "TO" default (what to suggest)
 ─────────────────────────┼─────────────────────────────┼──────────────────────────────────
 1 template button        │ config values               │ origin → new owner/repo  ✅
 2 gh --template          │ config values               │ origin → new owner/repo  ✅
 3 clone-reinit (no orig.)│ config values               │ no origin → git config only
 4 FORK                   │ config values  ⚠ NOT origin │ origin owner = forker (ok as a
   origin=forker/<tmpl>   │   (owner is the template's, │   default) BUT repo name still ==
                          │    from config)             │   <template> → COLLIDES → prompt
 5 ZIP (no git)           │ config values               │ no git → all prompts, no defaults
```

A fork's `origin` actively lies about the "from" side: deriving the old owner from `origin` would
read `<forker>` and then fail to replace the template's real owner, leaving template identity baked
into the new repo. Hence D2a (explicit/invariant "from"). The "to" defaults read git but guard the
fork-collision and missing-origin cases.

---

## 8. Safety and instantiation modes

- **git is the undo button.** Require a clean working tree (`--allow-dirty` overrides). No internal
  rollback — on apply failure, instruct `git checkout . && git clean -fd`.
- **Require `.git`.** The ZIP-download mode must `git init` first; `--allow-dirty` does **not**
  override the missing-`.git` precondition (the dirty-tree check presupposes a tree exists).
- **One-shot marker.** Refuse if the marker exists (`--force` overrides). The marker records the
  identity used + engine version + date — all `doctor` needs.
- **`--dry-run`** prints the full plan without writing. **`--config answers.toml`** drives headless
  / CI runs and is what the test suite uses.
- **Five instantiation modes** (template button, `gh --template`, clone-reinit, fork, ZIP) are a
  regression contract — one fixture per mode, asserting the guard's skip decision and `init`'s
  precondition handling. Modes are a property of git state, so they are tested identically
  regardless of delivery mechanism.

---

## 9. Post-init service wiring (split out — D3)

The source system's `post_init.py` bundles two sub-concerns with opposite lifecycles. They split:

```
  ┌─ A. DECLARATIVE GitHub/repo config ──────────────┐   ┌─ B. SaaS trust / import ──────┐
  │   • Actions secrets (e.g. CODECOV_TOKEN)         │   │  • PyPI OIDC trusted publisher │
  │   • environments (release / pypi)                │   │  • ReadTheDocs project import  │
  │   • branch protection, labels, repo settings     │   │  • Codecov app authorization   │
  │   • workflow enable/disable                       │   │                                │
  └──────────────────────────────────────────────────┘   └────────────────────────────────┘
         ▼ has a mature tool                                      ▼ irreducibly interactive
   LEVERAGE Terraform/OpenTofu                             keep a THIN walkthrough (~100 lines)
   (idempotent · drift-detectable · not our code)          (print exact form values + poll
                                                            until trust goes live)
```

- **A → Terraform/OpenTofu GitHub provider** (`integrations/github`): `github_actions_secret`,
  `github_repository_environment`, `github_branch_protection`, variables, labels. Declarative,
  idempotent, re-runnable. Shipped as a small `*.tf` module in the template; `identikit` core does
  not touch it. (Lighter alternative for repo *settings only*, no secrets: the Settings GitHub App
  syncing from `.github/settings.yml`.)
- **B → thin walkthrough.** PyPI trusted publishing has no IaC provider — it is a one-time web form
  (the "pending publisher"). The source system's "print the form values + poll until trust is live"
  pattern is about as good as it gets; keep it. RTD import and Codecov authorize are similarly
  one-time interactive.

Net: ~80% of `post_init.py` is designed out of `identikit`. The remaining ~20% can ship as a
separate optional walkthrough (an `identikit`-adjacent plugin or just docs), never in the rebrand
core.

The deep reason for the split: **rebrand is one-shot and destructive** (cannot be re-run), but
**service config is declarative and idempotent** (you *want* to re-run it as the project evolves).
Opposite lifecycles → different tools.

---

## 10. CLI surface (proposed)

Small, few verbs (mirrors the `claim-pypi` shape):

```
identikit discover [-o identikit.toml] [--summary]   # author: scan repo, emit/refresh config
identikit init [--config answers.toml] [--dry-run]   # creator: rebrand in place
               [--force] [--allow-dirty] [--commit] [--yes]
identikit doctor [--json]                            # audit: no "from" identity leaks
identikit prune                                      # remove identikit footprint post-init
```

---

## 11. Open build-time items

These are implementation details, not design forks:

- The `discover` scan algorithm (structured-vs-text mode heuristic, rename/regenerate detection,
  binary-file handling, bootstrap-dir exclusion).
- The structured-vs-text rewrite dispatch (`tomlkit` for TOML, targeted line edits for known
  formats, longest-first text replacement for prose; the empty `_rewriters` registry seam from the
  source system should not be shipped empty).
- The guard plugin interface across build tools (`just` eager `shell()` eval, `make`, npm scripts).
- The `[identity.*].validate` vocabulary (`python_identifier`, `repo_name`, `command_name`,
  `github_owner`, `email`, …).
- Collapsing the source system's `MODES` triplication (Python + shell runner + CI matrix) into one
  config/data file.

---

## 12. Naming

`identikit` — verified AVAILABLE on PyPI (no similar-name collisions) and reserved. PyPI dist name
`identikit` → import package `identikit` (valid snake-case identifier, no normalization surprise).
CLI command `identikit` (short alias `idkit` optional). GitHub repo `smorinlabs/identikit` (public).
