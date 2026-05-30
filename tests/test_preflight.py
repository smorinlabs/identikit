"""Tests for identikit.preflight — init preconditions across instantiation modes."""

from __future__ import annotations

import pytest

from identikit import marker, preflight


def test_missing_git_is_refused(tmp_path):
    # mode 5 (ZIP): no .git → refuse, even with --allow-dirty.
    state = preflight.GitState(has_git=False, is_dirty=False)
    with pytest.raises(preflight.PreconditionError, match="git init"):
        preflight.check_preconditions(tmp_path, state, force=False, allow_dirty=True)


def test_dirty_tree_is_refused_without_allow_dirty(tmp_path):
    state = preflight.GitState(has_git=True, is_dirty=True)
    with pytest.raises(preflight.PreconditionError, match="dirty"):
        preflight.check_preconditions(tmp_path, state, force=False, allow_dirty=False)


def test_dirty_tree_allowed_with_flag(tmp_path):
    state = preflight.GitState(has_git=True, is_dirty=True)
    preflight.check_preconditions(tmp_path, state, force=False, allow_dirty=True)


def test_existing_marker_refused_without_force(tmp_path):
    marker.write_marker(tmp_path, {"x": "y"}, version="0.1.0", date="2026-05-29")
    state = preflight.GitState(has_git=True, is_dirty=False)
    with pytest.raises(preflight.PreconditionError, match="already initialized"):
        preflight.check_preconditions(tmp_path, state, force=False, allow_dirty=False)


def test_existing_marker_allowed_with_force(tmp_path):
    marker.write_marker(tmp_path, {"x": "y"}, version="0.1.0", date="2026-05-29")
    state = preflight.GitState(has_git=True, is_dirty=False)
    preflight.check_preconditions(tmp_path, state, force=True, allow_dirty=False)


def test_clean_repo_passes(tmp_path):
    state = preflight.GitState(has_git=True, is_dirty=False)
    preflight.check_preconditions(tmp_path, state, force=False, allow_dirty=False)
