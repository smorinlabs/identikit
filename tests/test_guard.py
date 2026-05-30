"""Tests for the reference guard.sh — warn/block skip logic."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parent.parent / "guard.sh"


def _run(mode: str, marker: Path, origin: str, *skips: str):
    return subprocess.run(
        ["bash", str(GUARD), mode, str(marker), origin, *skips],
        capture_output=True,
        text=True,
    )


def test_warn_always_exits_zero(tmp_path):
    r = _run("warn", tmp_path / "absent", "git@github.com:acme/new.git")
    assert r.returncode == 0
    assert "identikit init" in r.stderr  # banner shown when not skipped


def test_warn_silent_when_marker_present(tmp_path):
    marker = tmp_path / ".identikit-initialized"
    marker.write_text("x", "utf-8")
    r = _run("warn", marker, "git@github.com:acme/new.git")
    assert r.returncode == 0
    assert r.stderr.strip() == ""  # already initialized → silent


def test_block_exits_nonzero_when_unmigrated(tmp_path):
    r = _run("block", tmp_path / "absent", "git@github.com:acme/new.git")
    assert r.returncode == 1


def test_block_skips_when_origin_matches_template(tmp_path):
    r = _run(
        "block",
        tmp_path / "absent",
        "git@github.com:smorinlabs/py-launch-blueprint.git",
        "smorinlabs/py-launch-blueprint",
    )
    assert r.returncode == 0  # contributing on the template itself → don't block


def test_block_does_not_skip_for_fork(tmp_path):
    # fork: same repo name, different owner → must still block (mode 4).
    r = _run(
        "block",
        tmp_path / "absent",
        "git@github.com:forker/py-launch-blueprint.git",
        "smorinlabs/py-launch-blueprint",
    )
    assert r.returncode == 1


def test_unknown_mode_errors(tmp_path):
    r = _run("frobnicate", tmp_path / "absent", "")
    assert r.returncode == 2


pytestmark = pytest.mark.integration
