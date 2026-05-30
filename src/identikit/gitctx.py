"""Thin git adapters — the only place identikit shells out to read git state."""

from __future__ import annotations

import subprocess
from pathlib import Path

from identikit.preflight import GitState


def _run(args: list[str], root: Path) -> str:
    try:
        r = subprocess.run(  # noqa: S603
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def has_git(root: Path) -> bool:
    return (Path(root) / ".git").exists()


def is_dirty(root: Path) -> bool:
    return bool(_run(["status", "--porcelain"], root))


def git_state(root: Path) -> GitState:
    return GitState(has_git=has_git(root), is_dirty=is_dirty(root))


def origin_url(root: Path) -> str:
    return _run(["remote", "get-url", "origin"], root)


def user_name(root: Path) -> str:
    return _run(["config", "--get", "user.name"], root)


def user_email(root: Path) -> str:
    return _run(["config", "--get", "user.email"], root)
