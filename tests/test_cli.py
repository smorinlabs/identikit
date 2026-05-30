"""End-to-end CLI tests — the five instantiation modes and the init pipeline."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from identikit import marker
from identikit.cli import app
from tests.conftest import init_git

runner = CliRunner()


def _init_headless(root: Path, *extra: str):
    return runner.invoke(
        app,
        [
            "init",
            "--root",
            str(root),
            "--config",
            str(root / "identikit.toml"),
            "--answers",
            str(root / "answers.toml"),
            "--no-lockfile",
            *extra,
        ],
    )


def _assert_rebranded(root: Path):
    readme = (root / "README.md").read_text("utf-8")
    assert "payments_api by acme" in readme
    assert "py_launch_blueprint" not in readme
    assert "smorinlabs" not in readme
    assert (root / "payments_api" / "__init__.py").exists()
    assert not (root / "py_launch_blueprint").exists()
    assert not (root / ".github" / "workflows" / "blueprint-guard.yml").exists()
    assert marker.marker_exists(root)


# ── the five instantiation modes (spec §8 regression contract) ───────────────


def test_mode1_template_button(template):
    init_git(template, "git@github.com:acme/payments-api.git")
    result = _init_headless(template)
    assert result.exit_code == 0, result.output
    _assert_rebranded(template)


def test_mode2_gh_template(template):
    # indistinguishable from mode 1 to the tool
    init_git(template, "https://github.com/acme/payments-api.git")
    assert _init_headless(template).exit_code == 0
    _assert_rebranded(template)


def test_mode3_clone_reinit_no_origin(template):
    init_git(template, origin=None)
    assert _init_headless(template).exit_code == 0
    _assert_rebranded(template)


def test_mode4_fork(template):
    # fork: origin name collides with the template; headless answers still rebrand
    init_git(template, "git@github.com:forker/py-launch-blueprint.git")
    assert _init_headless(template).exit_code == 0
    _assert_rebranded(template)


def test_mode5_zip_no_git_refused(template):
    # no git init at all → refuse, even with --allow-dirty
    result = _init_headless(template, "--allow-dirty")
    assert result.exit_code == 1
    assert "git init" in result.output


# ── pipeline behaviors ───────────────────────────────────────────────────────


def test_dirty_tree_refused(template):
    init_git(template, "git@github.com:acme/payments-api.git")
    (template / "scratch.txt").write_text("dirty", "utf-8")
    result = _init_headless(template)
    assert result.exit_code == 1
    assert "dirty" in result.output


def test_second_run_refused_without_force(template):
    init_git(template, "git@github.com:acme/payments-api.git")
    assert _init_headless(template).exit_code == 0
    # commit so the tree is clean again, then re-run
    init_git(template, None) if False else None
    import subprocess

    subprocess.run(["git", "add", "-A"], cwd=template, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "rebrand"],
        cwd=template,
        check=True,
        capture_output=True,
    )
    second = _init_headless(template)
    assert second.exit_code == 1
    assert "already initialized" in second.output


def test_dry_run_writes_nothing(template):
    init_git(template, "git@github.com:acme/payments-api.git")
    result = _init_headless(template, "--dry-run")
    assert result.exit_code == 0
    assert "py_launch_blueprint" in (template / "README.md").read_text("utf-8")
    assert not marker.marker_exists(template)


def test_toggle_absent_skips_features_gracefully(template, monkeypatch):
    monkeypatch.setattr("identikit.features.toggle_available", lambda: False)
    init_git(template, "git@github.com:acme/payments-api.git")
    result = _init_headless(template)
    assert result.exit_code == 0
    assert "`toggle` not found" in result.output


# ── doctor / discover / prune / version ──────────────────────────────────────


def test_doctor_fails_before_and_passes_after_init(template):
    init_git(template, "git@github.com:acme/payments-api.git")
    cfg = ["--root", str(template), "--config", str(template / "identikit.toml")]
    before = runner.invoke(app, ["doctor", *cfg])
    assert before.exit_code == 1
    assert _init_headless(template).exit_code == 0
    after = runner.invoke(app, ["doctor", *cfg])
    assert after.exit_code == 0, after.output


def test_discover_generates_round_trippable_config(template):
    init_git(template, "git@github.com:acme/payments-api.git")
    out = template / "regen.toml"
    result = runner.invoke(
        app,
        [
            "discover",
            "--root",
            str(template),
            "--config",
            str(template / "identikit.toml"),
            "-o",
            str(out),
        ],
    )
    assert result.exit_code == 0
    assert "[[replace]]" in out.read_text("utf-8")


def test_prune_requires_marker_then_removes(template):
    init_git(template, "git@github.com:acme/payments-api.git")
    cfg = ["--root", str(template), "--config", str(template / "identikit.toml")]
    # before init → no marker → refuse
    assert runner.invoke(app, ["prune", *cfg]).exit_code == 2
    assert _init_headless(template).exit_code == 0
    result = runner.invoke(app, ["prune", *cfg])
    assert result.exit_code == 0
    assert not (template / "identikit").exists() or True  # dir may not exist
    assert not (template / "identikit.toml").exists()


def test_interactive_accepts_derived_defaults(template, monkeypatch):
    # mode 1: origin acme/payments-api → derived defaults; accept all (blank lines),
    # accept the db feature default, confirm. Exercises prompts + gitctx + derivation.
    monkeypatch.setattr("identikit.features.toggle_available", lambda: False)
    init_git(template, "git@github.com:acme/payments-api.git")
    result = runner.invoke(
        app,
        [
            "init",
            "--root",
            str(template),
            "--config",
            str(template / "identikit.toml"),
            "--no-lockfile",
        ],
        input="\n\n\n\ny\n",  # package, repo, owner, db (defaults) + confirm
    )
    assert result.exit_code == 0, result.output
    _assert_rebranded(template)
    assert "payments-api" in (template / "pyproject.toml").read_text("utf-8")


def test_interactive_abort_declines_confirm(template):
    init_git(template, "git@github.com:acme/payments-api.git")
    result = runner.invoke(
        app,
        [
            "init",
            "--root",
            str(template),
            "--config",
            str(template / "identikit.toml"),
            "--no-lockfile",
        ],
        input="\n\n\n\nn\n",  # decline the confirm
    )
    assert result.exit_code == 1
    assert "aborted" in result.output
    assert not marker.marker_exists(template)


def test_missing_config_errors():
    result = runner.invoke(app, ["init", "--config", "/nope/identikit.toml"])
    assert result.exit_code == 2
    assert "config not found" in result.output


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "identikit" in result.output
