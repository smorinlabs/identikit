"""The one-shot init marker — a committed record of the rebrand.

Written once by `init` on success; read by `init` (to refuse a second run) and
by `doctor`. It is a pure gate + record, not a live map (the design is one-shot,
spec D0).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

MARKER_NAME = ".identikit-initialized"


def marker_path(root: Path) -> Path:
    return Path(root) / MARKER_NAME


def marker_exists(root: Path) -> bool:
    return marker_path(root).exists()


def write_marker(root: Path, answers: dict[str, str], version: str, date: str) -> Path:
    """Write the marker as TOML: ``[meta]`` + ``[answers]``."""
    lines = [
        f"# {MARKER_NAME} — written by identikit on a successful init.",
        "# Tracked by git; read by identikit init (refuse re-run) and doctor.",
        "",
        "[meta]",
        f'version = "{version}"',
        f'date    = "{date}"',
        "",
        "[answers]",
    ]
    lines += [f'{k} = "{v}"' for k, v in answers.items()]
    path = marker_path(root)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def read_marker(root: Path) -> dict | None:
    """Parse the marker, or None if absent."""
    path = marker_path(root)
    if not path.exists():
        return None
    return tomllib.loads(path.read_text(encoding="utf-8"))
