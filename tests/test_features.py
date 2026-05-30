"""Tests for identikit.features — graceful `toggle` feature/variant gating (D4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from identikit import common, features


def _config():
    return common.Config(
        features={
            "db": common.FeatureGroup("db", ("sqlite", "postgres"), "db?", "sqlite"),
            "codecov": common.FeatureGroup("codecov", ("on", "off"), "codecov?", "off"),
        }
    )


def test_toggle_command_targets_group_variant_over_tree():
    cmd = features.toggle_command("db", "postgres", Path("/repo"))
    assert cmd == ["toggle", "-S", "db:postgres", "-R", "/repo"]


def test_apply_features_invokes_toggle_per_selection_when_available(tmp_path):
    calls: list[list[str]] = []
    report = features.apply_features(
        _config(),
        {"db": "postgres", "codecov": "on"},
        root=tmp_path,
        runner=lambda cmd, cwd: calls.append(cmd),
        available=True,
    )
    assert ["toggle", "-S", "db:postgres", "-R", str(tmp_path)] in calls
    assert ["toggle", "-S", "codecov:on", "-R", str(tmp_path)] in calls
    assert report.activated == [("db", "postgres"), ("codecov", "on")]
    assert report.skipped_no_toggle is False


def test_apply_features_skips_gracefully_when_toggle_absent(tmp_path):
    calls: list[list[str]] = []
    report = features.apply_features(
        _config(),
        {"db": "postgres"},
        root=tmp_path,
        runner=lambda cmd, cwd: calls.append(cmd),
        available=False,
    )
    assert calls == []  # never shell out when the binary is missing
    assert report.skipped_no_toggle is True
    assert report.activated == []


def test_apply_features_rejects_unknown_variant(tmp_path):
    with pytest.raises(ValueError, match="mysql"):
        features.apply_features(
            _config(),
            {"db": "mysql"},
            root=tmp_path,
            runner=lambda cmd, cwd: None,
            available=True,
        )


def test_apply_features_rejects_unknown_group(tmp_path):
    with pytest.raises(ValueError, match="cache"):
        features.apply_features(
            _config(),
            {"cache": "redis"},
            root=tmp_path,
            runner=lambda cmd, cwd: None,
            available=True,
        )


def test_default_selections_uses_group_defaults():
    assert features.default_selections(_config()) == {"db": "sqlite", "codecov": "off"}
