"""Regression guard for the shipped example configs."""

from __future__ import annotations

from pathlib import Path

from identikit import common

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_py_launch_blueprint_example_is_coherent():
    cfg = common.load_config(EXAMPLES / "py-launch-blueprint" / "identikit.toml")

    # every replace/rename references a real identity field
    for op in cfg.replaces:
        assert op.field in cfg.identity, f"replace field {op.field!r} not in identity"
        assert op.mode in {"text", "structured"}

    # every validator name is one identikit actually knows (or "" = free text)
    for ident in cfg.identity.values():
        assert ident.validate == "" or ident.validate in common.VALIDATORS

    # rename templates only reference known fields
    for ren in cfg.renames:
        for token in _braced_tokens(ren.dst):
            assert token in cfg.identity, f"rename references unknown field {token!r}"

    assert cfg.from_values()["package_name"] == "py_launch_blueprint"
    assert "smorinlabs/py-launch-blueprint" in cfg.guard.skip_if_origin


def _braced_tokens(text: str) -> list[str]:
    import re

    return re.findall(r"\{(\w+)\}", text)
