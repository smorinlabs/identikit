"""Tests for identikit.common — config model, validators, origin parsing."""

from __future__ import annotations

import pytest

from identikit import common

# ── validators ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "validator,value",
    [
        ("python_identifier", "my_pkg"),
        ("python_identifier", "pkg2"),
        ("repo_name", "my-repo"),
        ("command_name", "my-cli"),
        ("github_owner", "smorinlabs"),
        ("github_owner", "a"),
        ("email", "a@b.co"),
    ],
)
def test_validators_accept_valid(validator, value):
    assert common.validate_value(validator, value) == value


@pytest.mark.parametrize(
    "validator,value",
    [
        ("python_identifier", "My-Pkg"),  # hyphen + capital
        ("python_identifier", "2pkg"),  # leading digit
        ("repo_name", "Repo_Name"),  # underscore + capital
        ("github_owner", "-bad"),  # leading hyphen
        ("github_owner", "x" * 40),  # too long
        ("email", "not-an-email"),
    ],
)
def test_validators_reject_invalid(validator, value):
    with pytest.raises(common.ValidationError):
        common.validate_value(validator, value)


def test_unknown_validator_is_a_noop_passthrough():
    # An empty / unknown validator name means "no constraint" (free-text fields).
    assert common.validate_value("", "anything at all") == "anything at all"


# ── origin parsing ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/smorinlabs/identikit", ("smorinlabs", "identikit")),
        ("https://github.com/smorinlabs/identikit.git", ("smorinlabs", "identikit")),
        ("git@github.com:smorinlabs/identikit.git", ("smorinlabs", "identikit")),
        ("git@github.com:smorinlabs/identikit", ("smorinlabs", "identikit")),
        ("", None),
        ("not a url", None),
    ],
)
def test_parse_origin(url, expected):
    assert common.parse_origin(url) == expected


def test_origin_matches_uses_owner_and_repo_not_name_alone():
    patterns = ("smorinlabs/py-launch-blueprint",)
    # exact owner+repo → match
    assert common.origin_matches(
        "git@github.com:smorinlabs/py-launch-blueprint.git", patterns
    )
    # fork: same repo name, different owner → must NOT match (mode 4)
    assert not common.origin_matches(
        "git@github.com:someone/py-launch-blueprint.git", patterns
    )
    # no origin → no match (mode 3 / 5)
    assert not common.origin_matches("", patterns)


# ── config loading ───────────────────────────────────────────────────────────

SAMPLE_CONFIG = """
[identity.package_name]
value    = "py_launch_blueprint"
validate = "python_identifier"
prompt   = "Python package name"

[identity.repo_name]
value    = "py-launch-blueprint"
validate = "repo_name"
prompt   = "repo name"
derive   = ""

[[replace]]
field = "package_name"
files = ["pyproject.toml", "src/py_launch_blueprint/__init__.py"]
mode  = "structured"

[[rename]]
from = "py_launch_blueprint"
to   = "{package_name}"

[[remove]]
path   = ".github/workflows/blueprint-guard.yml"
reason = "guard CI is template-only"

[[regenerate]]
path    = "uv.lock"
command = ["uv", "lock"]

[features.db]
variants = ["sqlite", "postgres"]
prompt   = "database driver?"
default  = "sqlite"

[guard]
skip_if_origin = ["smorinlabs/py-launch-blueprint"]
block          = ["build", "publish"]

[prune]
paths = ["identikit/"]
"""


def _write_config(tmp_path):
    p = tmp_path / "identikit.toml"
    p.write_text(SAMPLE_CONFIG, encoding="utf-8")
    return p


def test_load_config_parses_identity_as_field_map(tmp_path):
    cfg = common.load_config(_write_config(tmp_path))
    assert set(cfg.identity) == {"package_name", "repo_name"}
    assert cfg.identity["package_name"].value == "py_launch_blueprint"
    assert cfg.identity["package_name"].validate == "python_identifier"
    assert cfg.identity["repo_name"].prompt == "repo name"


def test_load_config_parses_operations(tmp_path):
    cfg = common.load_config(_write_config(tmp_path))
    assert cfg.replaces[0].field == "package_name"
    assert cfg.replaces[0].mode == "structured"
    assert "pyproject.toml" in cfg.replaces[0].files
    assert cfg.renames[0].src == "py_launch_blueprint"
    assert cfg.renames[0].dst == "{package_name}"
    assert cfg.removes[0].path == ".github/workflows/blueprint-guard.yml"
    assert cfg.regenerates[0].command == ("uv", "lock")


def test_load_config_parses_features_and_guard(tmp_path):
    cfg = common.load_config(_write_config(tmp_path))
    assert cfg.features["db"].variants == ("sqlite", "postgres")
    assert cfg.features["db"].default == "sqlite"
    assert cfg.guard.skip_if_origin == ("smorinlabs/py-launch-blueprint",)
    assert cfg.guard.block == ("build", "publish")
    assert cfg.prune == ("identikit/",)


def test_from_values_returns_field_to_value_map(tmp_path):
    cfg = common.load_config(_write_config(tmp_path))
    assert cfg.from_values() == {
        "package_name": "py_launch_blueprint",
        "repo_name": "py-launch-blueprint",
    }
