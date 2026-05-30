# Releasing identikit

The release pipeline mirrors `py-launch-blueprint`: **release-please** opens a
version PR from Conventional Commits; merging it tags `vX.Y.Z`; the tag triggers
**OIDC Trusted Publishing** to PyPI (no API tokens stored).

## Flow

```
 commits to main ──▶ release-please PR (bumps pyproject version + CHANGELOG)
        │                        │ merge
        │                        ▼
        │                 tag vX.Y.Z pushed
        │                        │
        ▼                        ▼
   CI (lint+test)         publish.yml: build → publish-pypi (OIDC)
```

## One-time setup

### 1. PyPI Trusted Publisher (OIDC)

`identikit` is already reserved on PyPI. Add a trusted publisher so the tag can
publish without a token — PyPI → *Manage* → *Publishing* → *Add a new pending/
trusted publisher*:

| Field | Value |
|---|---|
| Owner | `smorinlabs` |
| Repository | `identikit` |
| Workflow | `publish.yml` |
| Environment | `pypi` |

Then create the **`pypi`** environment in GitHub repo settings (Settings →
Environments → New environment → `pypi`); the `publish-pypi` job runs there.

### 2. release-please auth (one of two)

release-please must use credentials that can open PRs **and** trigger the
downstream `publish.yml` (the default `GITHUB_TOKEN` does neither reliably):

- **Preferred — GitHub App:** create an App with *Contents: write* +
  *Pull requests: write*, install it on the repo, and set repo secrets
  `RELEASE_PLEASE_APP_ID` and `RELEASE_PLEASE_PRIVATE_KEY`.
- **Fallback — PAT:** set `RELEASE_PLEASE_APP_TOKEN` to a fine-grained PAT with
  *Contents* + *Pull requests: write*.

With neither set, the release-please job fails fast.

### 3. Codecov (optional)

Set `CODECOV_TOKEN` to upload coverage; CI is `fail_ci_if_error: false`, so a
missing token only skips the upload.

## Cutting a release

1. Land Conventional-Commit changes on `main` (`feat:`, `fix:`, …).
2. Merge the release-please PR it opens.
3. The `vX.Y.Z` tag triggers `publish.yml` → PyPI. Verify:
   `uvx identikit --version` once it lands.

`publish.yml` refuses to publish if the tag isn't reachable from `main` or if the
tag doesn't match `[project].version` in `pyproject.toml`.
