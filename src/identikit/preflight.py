"""Init preconditions — the §8 safety checks across instantiation modes.

git is the undo button, so the tree must be a git repo and clean (overridable).
The marker enforces the one-shot rule. ``GitState`` is injected so the checks are
pure and testable without a real repo.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from identikit.marker import marker_exists


class PreconditionError(RuntimeError):
    """A precondition for running init was not met."""


@dataclass(frozen=True)
class GitState:
    has_git: bool
    is_dirty: bool


def check_preconditions(
    root: Path, git: GitState, *, force: bool, allow_dirty: bool
) -> None:
    """Raise ``PreconditionError`` if init must not proceed."""
    if not git.has_git:
        raise PreconditionError(
            "no .git directory found — this looks like a ZIP download (mode 5). "
            "Run `git init` first; git is the undo button this tool relies on. "
            "(--allow-dirty does NOT override this.)"
        )
    if marker_exists(root) and not force:
        raise PreconditionError(
            "already initialized (marker present). Pass --force to re-run."
        )
    if git.is_dirty and not allow_dirty:
        raise PreconditionError(
            "git working tree is dirty. Commit or stash, then re-run. "
            "(Pass --allow-dirty to override — but git is your undo button.)"
        )
