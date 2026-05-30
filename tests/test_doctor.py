"""Tests for identikit.doctor — post-rebrand no-leak audit."""

from __future__ import annotations

from identikit import common, doctor


def _config():
    return common.Config(
        identity={
            "package_name": common.IdentityField(
                "package_name", "py_launch_blueprint", "python_identifier"
            ),
            "owner": common.IdentityField("owner", "smorinlabs", "github_owner"),
        }
    )


def test_detects_leftover_from_value(tmp_path):
    (tmp_path / "README.md").write_text("still py_launch_blueprint here", "utf-8")
    report = doctor.check_no_leak(_config(), root=tmp_path)
    assert not report.ok()
    assert any(leak.field == "package_name" for leak in report.leaks)


def test_passes_on_clean_tree(tmp_path):
    (tmp_path / "README.md").write_text("payments_api by acme", "utf-8")
    report = doctor.check_no_leak(_config(), root=tmp_path)
    assert report.ok()
    assert report.leaks == []


def test_ignores_excluded_dirs(tmp_path):
    git = tmp_path / ".git"
    git.mkdir()
    (git / "COMMIT_EDITMSG").write_text("py_launch_blueprint", "utf-8")
    report = doctor.check_no_leak(_config(), root=tmp_path)
    assert report.ok()


def test_ignores_config_and_bootstrap_paths(tmp_path):
    # The from-values legitimately live in the config file and bootstrap dir.
    (tmp_path / "identikit.toml").write_text('value = "py_launch_blueprint"', "utf-8")
    ik = tmp_path / "identikit"
    ik.mkdir()
    (ik / "notes.md").write_text("smorinlabs", "utf-8")
    report = doctor.check_no_leak(
        _config(), root=tmp_path, exclude_paths=("identikit.toml", "identikit")
    )
    assert report.ok()


def test_counts_occurrences(tmp_path):
    (tmp_path / "a.md").write_text("smorinlabs smorinlabs", "utf-8")
    report = doctor.check_no_leak(_config(), root=tmp_path)
    owner_leaks = [leak for leak in report.leaks if leak.field == "owner"]
    assert owner_leaks[0].count == 2
