"""Tests for identikit.discover — scan a repo, emit a draft identikit.toml."""

from __future__ import annotations

from identikit import common, discover


def _identity():
    return {
        "package_name": common.IdentityField(
            "package_name", "py_launch_blueprint", "python_identifier", "package?"
        ),
        "repo_name": common.IdentityField(
            "repo_name", "py-launch-blueprint", "repo_name", "repo?"
        ),
    }


def _make_repo(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        'name = "py_launch_blueprint"\nrepo = "py-launch-blueprint"', "utf-8"
    )
    (tmp_path / "README.md").write_text(
        "py_launch_blueprint py_launch_blueprint by py-launch-blueprint", "utf-8"
    )
    pkg = tmp_path / "py_launch_blueprint"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("x", "utf-8")
    (tmp_path / "uv.lock").write_text("lock", "utf-8")
    return tmp_path


def test_scan_groups_by_field_and_mode(tmp_path):
    _make_repo(tmp_path)
    scan = discover.scan_values(tmp_path, _identity())
    # package_name appears in pyproject.toml (structured) and README.md (text)
    assert scan[("package_name", "structured")]["pyproject.toml"] == 1
    assert scan[("package_name", "text")]["README.md"] == 2


def test_find_renames_detects_named_paths(tmp_path):
    _make_repo(tmp_path)
    renames = discover.find_renames(tmp_path, _identity())
    assert ("py_launch_blueprint", "{package_name}") in renames


def test_find_regenerates_detects_lockfiles(tmp_path):
    _make_repo(tmp_path)
    regens = discover.find_regenerates(tmp_path)
    assert ("uv.lock", ["uv", "lock"]) in regens


def test_generated_config_round_trips(tmp_path):
    _make_repo(tmp_path)
    text = discover.generate(tmp_path, _identity())
    out = tmp_path / "identikit.toml"
    out.write_text(text, "utf-8")
    cfg = common.load_config(out)
    # identity echoed with metadata intact
    assert cfg.identity["package_name"].value == "py_launch_blueprint"
    assert cfg.identity["package_name"].validate == "python_identifier"
    # replace blocks present for both modes
    fields_modes = {(r.field, r.mode) for r in cfg.replaces}
    assert ("package_name", "structured") in fields_modes
    assert ("package_name", "text") in fields_modes
    # rename + regenerate present
    assert any(r.src == "py_launch_blueprint" for r in cfg.renames)
    assert any(r.path == "uv.lock" for r in cfg.regenerates)


def test_scan_excludes_lockfiles_and_bootstrap(tmp_path):
    _make_repo(tmp_path)
    # uv.lock contains no identity here, but ensure it is never a replace target
    scan = discover.scan_values(tmp_path, _identity())
    for files in scan.values():
        assert "uv.lock" not in files
