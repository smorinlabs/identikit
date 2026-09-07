# identikit — name reservation inventory

Every GitHub repository and published package name in the `identikit` family, and the
rule that decides which registries each name is reserved on.

Verified live against GitHub, npm, PyPI, and crates.io on **2026-09-07**.

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
| `identikit` | 2026-05-29 | https://pypi.org/project/identikit/ |
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

- **PyPI placeholders carry a reclaim risk, via one of two distinct paths.** PEP 541 has no
  standalone "bare placeholder" rule. What it has is (a) *invalid* projects, which include
  "name squatting (package has no functionality or is empty)" — the path a bare placeholder is
  actually exposed to; and (b) *abandoned* project transfer, a much higher bar requiring all of:
  the project meets the abandonment criteria, the claimant demonstrates failed attempts to
  contact the owner, the claimant's own project already exists and meets notability
  requirements, a fork under a different name is not an acceptable workaround, download
  statistics show the existing package is unused, and the index maintainers have no further
  reservations. The 5 PyPI entries are a hold, not a deed — ship something real before it
  matters. See <https://peps.python.org/pep-0541/>.
- **crates.io reservations are permanent.** A published crate can be yanked from resolution
  but the name is never released. The 4 crates are held for good.
- **npm placeholders remain removable; their exact versions do not.** The free 72-hour
  unpublish window has closed, but that is not npm's only unpublish path: after 72 hours npm
  still permits unpublishing a package with no dependents in the public registry, fewer than
  300 downloads in the last week, and a single owner — conditions these placeholders currently
  meet. What is permanent is the exact `name@version` pair: once `identikit@0.0.1` has been
  published, that version string can never be used again, even after an unpublish. Removing
  every version of a package also blocks republishing that name for 24 hours. See
  <https://docs.npmjs.com/policies/unpublish/>.
- **The first real release must sort above the placeholder** in each ecosystem: npm above
  `0.0.1`, PyPI above `0.0.0.dev0`, crates.io above `0.0.0`. npm is the one to watch: its
  placeholder already consumed `0.0.1`, so a first real release numbered `0.0.1` is rejected
  as a duplicate. Start at `0.0.2` or `0.1.0`.
- **The five sibling READMEs say "Intended registries."** That wording was written before the
  reservations ran. All reservations are now complete, so it can be updated to "Reserved on."
