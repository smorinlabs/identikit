"""The rewrite engine — resolve a Config against Answers, then apply in place.

Order of operations (spec §5.3): remove → replace → rename → regenerate.

- remove first shrinks the working set;
- replace runs while paths still match the manifest's `files` lists;
- rename runs last so no op sees a path under its new name;
- regenerate (lockfiles) runs after the new name exists.

Answers are a plain ``dict[str, str]`` keyed by identity-field name — the
field-agnostic representation that lets one engine serve any identity schema.
No internal rollback: on failure the CLI tells the user ``git checkout . &&
git clean -fd``. git is the undo button.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from identikit.common import Config, RenameOp, validate_value

Answers = dict[str, str]
Runner = Callable[[list[str], Path], object]


def validate_answers(config: Config, answers: Answers) -> None:
    """Validate one answer per identity field; raise on missing or invalid."""
    for name, ident in config.identity.items():
        if name not in answers:
            raise KeyError(f"missing answer for identity field {name!r}")
        validate_value(ident.validate, answers[name])


def replace_in_text(text: str, pairs: Iterable[tuple[str, str]]) -> str:
    """Apply ``(from, to)`` replacements longest-first.

    Longest-first defuses substring collisions between identity values (e.g.
    ``smorin`` inside ``smorinlabs``).
    """
    for src, dst in sorted(pairs, key=lambda kv: -len(kv[0])):
        if src and src != dst:
            text = text.replace(src, dst)
    return text


def _resolve_renames(renames: Iterable[RenameOp], answers: Answers) -> list[RenameOp]:
    """Substitute ``{field}`` placeholders in rename destinations."""
    resolved: list[RenameOp] = []
    for r in renames:
        dst = r.dst
        for k, v in answers.items():
            dst = dst.replace("{" + k + "}", v)
        resolved.append(RenameOp(src=r.src, dst=dst))
    return resolved


# ── plan ─────────────────────────────────────────────────────────────────────


@dataclass
class PlanItem:
    kind: str  # "remove" | "replace" | "rename"
    path: str
    detail: str

    def render(self) -> str:
        return f"  [{self.kind:<7}] {self.path}  —  {self.detail}"


@dataclass
class Plan:
    items: list[PlanItem] = field(default_factory=list)

    def render(self) -> str:
        if not self.items:
            return "(plan is empty — nothing to do)"
        return "\n".join(["Plan:", *(it.render() for it in self.items)])

    def counts(self) -> dict[str, int]:
        out = {"remove": 0, "replace": 0, "rename": 0}
        for it in self.items:
            out[it.kind] = out.get(it.kind, 0) + 1
        return out


def build_plan(config: Config, answers: Answers, root: Path) -> Plan:
    """Resolve the config against answers into a concrete, previewable plan."""
    validate_answers(config, answers)
    plan = Plan()
    from_values = config.from_values()

    for op in config.removes:
        state = "exists" if (root / op.path).exists() else "missing — skip"
        plan.items.append(PlanItem("remove", op.path, f"{op.reason} ({state})"))

    for op in config.replaces:
        src = from_values[op.field]
        dst = answers[op.field]
        for f in op.files:
            present = (root / f).exists()
            tail = f"{src!r}→{dst!r}" if present else "missing — skip"
            plan.items.append(
                PlanItem("replace", f, f"field={op.field} mode={op.mode}  {tail}")
            )

    for op in _resolve_renames(config.renames, answers):
        present = (root / op.src).exists()
        tail = f"→ {op.dst}" + ("" if present else " (missing — skip)")
        plan.items.append(PlanItem("rename", op.src, tail))

    return plan


# ── apply ────────────────────────────────────────────────────────────────────


@dataclass
class ApplyReport:
    removed: list[str] = field(default_factory=list)
    replaced: list[str] = field(default_factory=list)
    renamed: list[tuple[str, str]] = field(default_factory=list)
    regenerated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def render(self) -> str:
        return (
            f"Applied: {len(self.removed)} removed, {len(self.replaced)} replaced, "
            f"{len(self.renamed)} renamed, {len(self.regenerated)} regenerated, "
            f"{len(self.skipped)} skipped."
        )


def _default_runner(cmd: list[str], cwd: Path) -> object:
    return subprocess.run(cmd, cwd=cwd, check=False)  # noqa: S603


def apply(
    config: Config,
    answers: Answers,
    root: Path,
    runner: Runner = _default_runner,
) -> ApplyReport:
    """Execute remove → replace → rename → regenerate in place under ``root``."""
    validate_answers(config, answers)
    report = ApplyReport()
    from_values = config.from_values()

    for op in config.removes:
        target = root / op.path
        if not target.exists():
            report.skipped.append(f"remove {op.path} (missing)")
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        report.removed.append(op.path)

    for op in config.replaces:
        pair = (from_values[op.field], answers[op.field])
        for f in op.files:
            target = root / f
            if not target.exists():
                report.skipped.append(f"replace {f} (missing)")
                continue
            text = target.read_text(encoding="utf-8")
            new_text = replace_in_text(text, [pair])
            if new_text == text:
                report.skipped.append(f"replace {f} (no change)")
                continue
            target.write_text(new_text, encoding="utf-8")
            report.replaced.append(f)

    for op in _resolve_renames(config.renames, answers):
        src = root / op.src
        if not src.exists():
            report.skipped.append(f"rename {op.src} (missing)")
            continue
        dst = root / op.dst
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        report.renamed.append((op.src, op.dst))

    for op in config.regenerates:
        if not (root / op.path).exists():
            report.skipped.append(f"regenerate {op.path} (missing)")
            continue
        runner(list(op.command), root)
        report.regenerated.append(op.path)

    return report
