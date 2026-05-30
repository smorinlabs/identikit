"""Tests for identikit.rewriters — structured (tomlkit) replacement."""

from __future__ import annotations

import tomllib

from identikit import rewriters


def test_structured_toml_replaces_string_values(tmp_path):
    p = tmp_path / "pyproject.toml"
    p.write_text(
        "# annotation: keep this py_launch_blueprint note (ITM-026)\n"
        "[project]\n"
        'name = "py_launch_blueprint"\n'
        'deps = ["py_launch_blueprint", "other"]\n'
        "\n"
        "[tool.nested]\n"
        'pkg = "py_launch_blueprint.sub"\n',
        "utf-8",
    )
    changed = rewriters.rewrite_structured(p, "py_launch_blueprint", "payments_api")
    assert changed
    data = tomllib.loads(p.read_text("utf-8"))
    assert data["project"]["name"] == "payments_api"
    assert data["project"]["deps"][0] == "payments_api"
    assert data["tool"]["nested"]["pkg"] == "payments_api.sub"


def test_structured_toml_preserves_standalone_comment(tmp_path):
    # The whole point of structured mode: a comment occurrence is NOT rewritten,
    # and the document structure survives (text mode would hit the comment too).
    p = tmp_path / "pyproject.toml"
    p.write_text(
        "# annotation: keep this py_launch_blueprint note (ITM-026)\n"
        '[project]\nname = "py_launch_blueprint"\n',
        "utf-8",
    )
    rewriters.rewrite_structured(p, "py_launch_blueprint", "payments_api")
    text = p.read_text("utf-8")
    assert "# annotation: keep this py_launch_blueprint note (ITM-026)" in text
    assert 'name = "payments_api"' in text


def test_structured_no_match_returns_false(tmp_path):
    p = tmp_path / "pyproject.toml"
    p.write_text('[project]\nname = "other"\n', "utf-8")
    assert (
        rewriters.rewrite_structured(p, "py_launch_blueprint", "payments_api") is False
    )


def test_structured_non_toml_falls_back_to_text(tmp_path):
    p = tmp_path / "README.md"
    p.write_text("py_launch_blueprint here", "utf-8")
    changed = rewriters.rewrite_structured(p, "py_launch_blueprint", "payments_api")
    assert changed
    assert p.read_text("utf-8") == "payments_api here"
