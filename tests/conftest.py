"""Shared fixtures — a minimal template repo + git mode setup."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

CONFIG = """
[identity.package_name]
value    = "py_launch_blueprint"
validate = "python_identifier"
prompt   = "package name"
derive   = "repo_name|snake"

[identity.repo_name]
value    = "py-launch-blueprint"
validate = "repo_name"
prompt   = "repo name"
derive   = "origin.repo"

[identity.owner]
value    = "smorinlabs"
validate = "github_owner"
prompt   = "owner"
derive   = "origin.owner"

[[replace]]
field = "package_name"
files = ["pyproject.toml", "README.md", "py_launch_blueprint/__init__.py"]
mode  = "text"

[[replace]]
field = "repo_name"
files = ["pyproject.toml", "README.md"]
mode  = "text"

[[replace]]
field = "owner"
files = ["README.md"]
mode  = "text"

[[rename]]
from = "py_launch_blueprint"
to   = "{package_name}"

[[remove]]
path   = ".github/workflows/blueprint-guard.yml"
reason = "guard CI is template-only"

[features.db]
variants = ["sqlite", "postgres"]
prompt   = "database driver?"
default  = "sqlite"

[guard]
skip_if_origin = ["smorinlabs/py-launch-blueprint"]

[prune]
paths = ["identikit", "identikit.toml"]
"""

ANSWERS = """
[answers]
package_name = "payments_api"
repo_name    = "payments-api"
owner        = "acme"

[features]
db = "postgres"
"""


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def template(tmp_path: Path) -> Path:
    """A bare (non-git) template tree carrying blueprint identity."""
    root = tmp_path
    (root / "pyproject.toml").write_text(
        'name = "py_launch_blueprint"\nrepo = "py-launch-blueprint"\n', "utf-8"
    )
    (root / "README.md").write_text(
        "# py-launch-blueprint\n\npy_launch_blueprint by smorinlabs\n", "utf-8"
    )
    pkg = root / "py_launch_blueprint"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('"""py_launch_blueprint."""\n', "utf-8")
    wf = root / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "blueprint-guard.yml").write_text("on: push\n", "utf-8")
    (root / "identikit.toml").write_text(CONFIG, "utf-8")
    (root / "answers.toml").write_text(ANSWERS, "utf-8")
    return root


def init_git(root: Path, origin: str | None) -> None:
    _git(["init", "-q"], root)
    _git(["config", "user.name", "Ada Lovelace"], root)
    _git(["config", "user.email", "ada@example.com"], root)
    if origin:
        _git(["remote", "add", "origin", origin], root)
    _git(["add", "-A"], root)
    _git(["commit", "-q", "-m", "initial"], root)
