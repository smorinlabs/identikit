"""Tests for identikit.engine — plan building and in-place application."""

from __future__ import annotations

import pytest

from identikit import common, engine


def _config():
    return common.Config(
        identity={
            "package_name": common.IdentityField(
                "package_name", "py_launch_blueprint", "python_identifier"
            ),
            "repo_name": common.IdentityField(
                "repo_name", "py-launch-blueprint", "repo_name"
            ),
            "owner": common.IdentityField("owner", "smorinlabs", "github_owner"),
        },
        replaces=(
            common.ReplaceOp("package_name", ("pyproject.toml", "README.md"), "text"),
            common.ReplaceOp("owner", ("README.md",), "text"),
        ),
        renames=(common.RenameOp("py_launch_blueprint", "{package_name}"),),
        removes=(
            common.RemoveOp(".github/workflows/blueprint-guard.yml", "blueprint"),
        ),
    )


def _answers():
    return {
        "package_name": "payments_api",
        "repo_name": "payments-api",
        "owner": "acme",
    }


# ── answer validation ────────────────────────────────────────────────────────


def test_validate_answers_rejects_invalid_field():
    cfg = _config()
    bad = _answers() | {"package_name": "Bad-Name"}
    with pytest.raises(common.ValidationError):
        engine.validate_answers(cfg, bad)


def test_validate_answers_requires_every_identity_field():
    cfg = _config()
    incomplete = {"package_name": "payments_api"}
    with pytest.raises(KeyError):
        engine.validate_answers(cfg, incomplete)


# ── plan building ────────────────────────────────────────────────────────────


def test_build_plan_lists_removes_replaces_renames(tmp_path):
    (tmp_path / "pyproject.toml").write_text("name = py_launch_blueprint", "utf-8")
    (tmp_path / "README.md").write_text("py_launch_blueprint by smorinlabs", "utf-8")
    (tmp_path / "py_launch_blueprint").mkdir()
    plan = engine.build_plan(_config(), _answers(), root=tmp_path)
    kinds = plan.counts()
    assert kinds["remove"] == 1
    assert kinds["replace"] == 3  # package_name×2 files + owner×1 file
    assert kinds["rename"] == 1


def test_build_plan_marks_missing_files_as_skip(tmp_path):
    # No files created → every op should still appear, flagged missing.
    plan = engine.build_plan(_config(), _answers(), root=tmp_path)
    rendered = plan.render()
    assert "missing" in rendered


# ── apply: replace ───────────────────────────────────────────────────────────


def test_apply_replaces_text_occurrences(tmp_path):
    (tmp_path / "README.md").write_text("py_launch_blueprint by smorinlabs", "utf-8")
    (tmp_path / "pyproject.toml").write_text("name = py_launch_blueprint", "utf-8")
    engine.apply(_config(), _answers(), root=tmp_path, runner=_no_run)
    assert (tmp_path / "README.md").read_text("utf-8") == "payments_api by acme"
    assert (tmp_path / "pyproject.toml").read_text("utf-8") == "name = payments_api"


def test_replace_in_text_is_longest_first():
    # 'smorin' is a substring of 'smorinlabs'; longest-first prevents corruption.
    out = engine.replace_in_text(
        "smorinlabs and smorin",
        [("smorin", "X"), ("smorinlabs", "Y")],
    )
    assert out == "Y and X"


# ── apply: rename + remove ───────────────────────────────────────────────────


def test_apply_renames_directory_using_answer(tmp_path):
    pkg = tmp_path / "py_launch_blueprint"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("x", "utf-8")
    engine.apply(_config(), _answers(), root=tmp_path, runner=_no_run)
    assert not pkg.exists()
    assert (tmp_path / "payments_api" / "__init__.py").read_text("utf-8") == "x"


def test_apply_removes_listed_path(tmp_path):
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "blueprint-guard.yml").write_text("x", "utf-8")
    engine.apply(_config(), _answers(), root=tmp_path, runner=_no_run)
    assert not (wf / "blueprint-guard.yml").exists()


# ── apply: regenerate (dependency-injected runner) ───────────────────────────


def test_apply_invokes_regenerate_commands(tmp_path):
    cfg = common.Config(
        identity={
            "package_name": common.IdentityField(
                "package_name", "py_launch_blueprint", "python_identifier"
            )
        },
        regenerates=(common.RegenerateOp("uv.lock", ("uv", "lock")),),
    )
    (tmp_path / "uv.lock").write_text("lock", "utf-8")
    calls: list[list[str]] = []
    engine.apply(
        cfg,
        {"package_name": "payments_api"},
        root=tmp_path,
        runner=lambda cmd, cwd: calls.append(cmd),
    )
    assert calls == [["uv", "lock"]]


def test_apply_skips_regenerate_when_target_missing(tmp_path):
    cfg = common.Config(
        identity={
            "package_name": common.IdentityField(
                "package_name", "py_launch_blueprint", "python_identifier"
            )
        },
        regenerates=(common.RegenerateOp("uv.lock", ("uv", "lock")),),
    )
    calls: list[list[str]] = []
    engine.apply(
        cfg,
        {"package_name": "payments_api"},
        root=tmp_path,
        runner=lambda cmd, cwd: calls.append(cmd),
    )
    assert calls == []  # no uv.lock present → don't regenerate


def _no_run(cmd, cwd):  # pragma: no cover - regenerate not exercised in these tests
    raise AssertionError("runner should not be called")
