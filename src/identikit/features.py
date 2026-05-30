"""Feature/variant gating via the `toggle` binary (spec §9.5, decision D4).

identikit owns whole-file identity rewrite; the reversible, sub-file feature
dimension (activate a CI job, swap a DB driver) is delegated to `toggle`
(https://github.com/smorin/toggle), which comments/uncomments marked blocks in
place. Because a commented-out variant is still a valid file, this preserves the
no-tokens / live-CI-green property.

The coupling is intentionally *optional*: if the `toggle` binary is not on PATH,
`apply_features` skips with a note instead of failing, so identikit stays fully
usable via plain `uvx`.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from identikit.common import Config

Runner = Callable[[list[str], Path], object]

TOGGLE_BINARIES = ("toggle", "togl")


def toggle_available() -> bool:
    """True if a `toggle` binary is discoverable on PATH."""
    return any(shutil.which(name) for name in TOGGLE_BINARIES)


def toggle_command(group: str, variant: str, root: Path) -> list[str]:
    """Build the argv that activates ``group:variant`` across the tree."""
    return ["toggle", "-S", f"{group}:{variant}", "-R", str(root)]


def default_selections(config: Config) -> dict[str, str]:
    """The per-group default variant from config."""
    return {name: grp.default for name, grp in config.features.items()}


def _default_runner(cmd: list[str], cwd: Path) -> object:
    return subprocess.run(cmd, cwd=cwd, check=False)  # noqa: S603


@dataclass
class FeatureReport:
    activated: list[tuple[str, str]] = field(default_factory=list)
    skipped_no_toggle: bool = False

    def render(self) -> str:
        if self.skipped_no_toggle:
            return (
                "features: `toggle` not found on PATH — skipped variant activation. "
                "Install it (cargo install togl) and run `toggle -S <group>:<variant>`."
            )
        if not self.activated:
            return "features: none configured."
        picks = ", ".join(f"{g}:{v}" for g, v in self.activated)
        return f"features: activated {picks}."


def _validate_selections(config: Config, selections: dict[str, str]) -> None:
    for group, variant in selections.items():
        grp = config.features.get(group)
        if grp is None:
            raise ValueError(f"unknown feature group {group!r}")
        if variant not in grp.variants:
            raise ValueError(
                f"unknown variant {variant!r} for group {group!r} "
                f"(choices: {', '.join(grp.variants)})"
            )


def apply_features(
    config: Config,
    selections: dict[str, str],
    root: Path,
    runner: Runner = _default_runner,
    available: bool | None = None,
) -> FeatureReport:
    """Activate the selected variants via `toggle`, or skip gracefully.

    ``available`` overrides binary detection (used by tests); when None it is
    resolved from PATH.
    """
    _validate_selections(config, selections)
    if available is None:
        available = toggle_available()

    report = FeatureReport()
    if not available:
        report.skipped_no_toggle = True
        return report

    for group, variant in selections.items():
        runner(toggle_command(group, variant, root), root)
        report.activated.append((group, variant))
    return report
