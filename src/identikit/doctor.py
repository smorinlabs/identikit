"""Audit: confirm no "from" identity value leaked through a rebrand.

A clean run leaves zero occurrences of any identity field's *from* value anywhere
in the tree, except in the config file and bootstrap dirs (where those values
legitimately live as data). Any other occurrence is a leak — usually a file the
manifest forgot to list.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from identikit.common import Config

DEFAULT_EXCLUDE_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".uv-cache",
    }
)


def _is_binary(path: Path) -> bool:
    try:
        return b"\x00" in path.read_bytes()[:8192]
    except OSError:
        return True


def _excluded(rel: Path, exclude_paths: Iterable[str]) -> bool:
    if any(part in DEFAULT_EXCLUDE_DIRS for part in rel.parts):
        return True
    rel_str = str(rel)
    for ep in exclude_paths:
        ep = ep.rstrip("/")
        if rel_str == ep or rel_str.startswith(ep + "/"):
            return True
    return False


def iter_text_files(root: Path, exclude_paths: Iterable[str] = ()) -> Iterator[Path]:
    """Yield non-excluded, non-binary files under ``root``, sorted."""
    exclude_paths = tuple(exclude_paths)
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if _excluded(p.relative_to(root), exclude_paths):
            continue
        if _is_binary(p):
            continue
        yield p


@dataclass
class Leak:
    path: str
    field: str
    value: str
    count: int


@dataclass
class DoctorReport:
    leaks: list[Leak] = field(default_factory=list)

    def ok(self) -> bool:
        return not self.leaks

    def render(self) -> str:
        if self.ok():
            return "doctor: ✓ no leftover identity values found."
        lines = ["doctor: ✗ leftover identity values:"]
        for leak in self.leaks:
            lines.append(f"  {leak.path}: {leak.field}={leak.value!r} ×{leak.count}")
        return "\n".join(lines)


def check_no_leak(
    config: Config, root: Path, exclude_paths: Iterable[str] = ()
) -> DoctorReport:
    """Scan the tree for any remaining identity "from" value."""
    from_values = config.from_values()
    report = DoctorReport()
    for path in iter_text_files(root, exclude_paths):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = str(path.relative_to(root))
        for fieldname, value in from_values.items():
            count = text.count(value)
            if count:
                report.leaks.append(Leak(rel, fieldname, value, count))
    return report
