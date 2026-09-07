# identikit — name reservation inventory

Every GitHub repository and published package name in the `identikit` family, and the
rule that decides which registries each name is reserved on.

Verified live against GitHub, npm, PyPI, and crates.io on **2026-09-01**.

**Totals:** 6 GitHub repos · 14 package reservations across 3 registries.

---

## 1. GitHub repositories (6)

All under the `smorinlabs` org, all public, all MIT.

| Repo | Role | Created | URL |
|---|---|---|---|
| `identikit` | CLI (original) | 2026-05-29 | https://github.com/smorinlabs/identikit |
| `identikit-py` | CLI | 2026-08-25 | https://github.com/smorinlabs/identikit-py |
| `identikit-rs` | CLI | 2026-08-25 | https://github.com/smorinlabs/identikit-rs |
| `identikit-rslib` | library (Rust) | 2026-08-25 | https://github.com/smorinlabs/identikit-rslib |
| `identikit-pylib` | library (Python) | 2026-08-25 | https://github.com/smorinlabs/identikit-pylib |
| `identikit-tslib` | library (TypeScript) | 2026-08-25 | https://github.com/smorinlabs/identikit-tslib |

---

## 2. Coverage matrix

`✅` = reserved · `—` = deliberately not reserved (the package has no presence in that ecosystem)

| Name | Kind | npm | PyPI | crates.io |
|---|---|:--:|:--:|:--:|
| `identikit` | CLI | ✅ | ✅ | ✅ |
| `identikit-py` | CLI | ✅ | ✅ | ✅ |
| `identikit-rs` | CLI | ✅ | ✅ | ✅ |
| `identikit-rslib` | Rust lib + future bindings | ✅ | ✅ | ✅ |
| `identikit-pylib` | Python lib | — | ✅ | — |
| `identikit-tslib` | TypeScript lib | ✅ | — | — |
| **Total** | | **5** | **5** | **4** |

Rules behind the matrix:

- **CLIs take all three registries** so the tool installs from any ecosystem
  (`npx`, `pipx`/`uvx`, `cargo install`), regardless of the language it is written in.
- **Libraries take only their native registry**, because exactly one dependency solver
  resolves them (`package.json`, `pyproject.toml`, or `Cargo.toml`).
- **`identikit-rslib` is the exception.** crates.io is its native home; npm and PyPI are
  held for the TypeScript and Python bindings planned after V1.

---

## 3. npm — 5 packages

Placeholder version `0.0.1`, maintainer `smorin`.

| Package | Reserved | URL |
|---|---|---|
| `identikit` | 2026-08-19 | https://www.npmjs.com/package/identikit |
| `identikit-py` | 2026-08-25 | https://www.npmjs.com/package/identikit-py |
| `identikit-rs` | 2026-08-25 | https://www.npmjs.com/package/identikit-rs |
| `identikit-rslib` | 2026-08-25 | https://www.npmjs.com/package/identikit-rslib |
| `identikit-tslib` | 2026-08-25 | https://www.npmjs.com/package/identikit-tslib |

Not on npm: `identikit-pylib` (Python library — PyPI only).

---

## 4. PyPI — 5 packages

Placeholder version `0.0.0.dev0`.

| Package | Reserved | URL |
|---|---|---|
| `identikit` | 2026-08-19 | https://pypi.org/project/identikit/ |
| `identikit-py` | 2026-08-25 | https://pypi.org/project/identikit-py/ |
| `identikit-rs` | 2026-08-25 | https://pypi.org/project/identikit-rs/ |
| `identikit-rslib` | 2026-08-25 | https://pypi.org/project/identikit-rslib/ |
| `identikit-pylib` | 2026-08-25 | https://pypi.org/project/identikit-pylib/ |

Not on PyPI: `identikit-tslib` (TypeScript library — npm only).

---

## 5. crates.io — 4 crates

Placeholder version `0.0.0`.

| Crate | Reserved | URL |
|---|---|---|
| `identikit` | 2026-08-19 | https://crates.io/crates/identikit |
| `identikit-py` | 2026-08-25 | https://crates.io/crates/identikit-py |
| `identikit-rs` | 2026-08-25 | https://crates.io/crates/identikit-rs |
| `identikit-rslib` | 2026-08-25 | https://crates.io/crates/identikit-rslib |

Not on crates.io: `identikit-pylib`, `identikit-tslib` (no Rust presence).

---

## 6. Maintenance notes

- **PyPI placeholders are reclaimable.** PEP 541 lets PyPI maintainers reclaim a name whose
  only release is a bare placeholder. The 5 PyPI entries are a hold, not a deed — ship
  something real before it matters.
- **crates.io reservations are permanent.** A published crate can be yanked from resolution
  but the name is never released. The 4 crates are held for good.
- **npm's unpublish window has closed.** It runs 72 hours from publish; these were reserved
  2026-08-25, so they are now effectively permanent too.
- **The first real release must sort above the placeholder** in each ecosystem: npm above
  `0.0.1`, PyPI above `0.0.0.dev0`, crates.io above `0.0.0`. npm is the one to watch: its
  placeholder already consumed `0.0.1`, so a first real release numbered `0.0.1` is rejected
  as a duplicate. Start at `0.0.2` or `0.1.0`.
- **The five sibling READMEs say "Intended registries."** That wording was written before the
  reservations ran. All reservations are now complete, so it can be updated to "Reserved on."
