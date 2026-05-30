"""identikit CLI — discover / init / doctor / prune.

`init` orchestrates the pipeline from spec §5.3:
    preflight → answers → plan → preview → apply → features → marker → lockfiles
"""

from __future__ import annotations

import datetime as _dt
import shutil
import tomllib
from dataclasses import replace as dc_replace
from pathlib import Path

import typer

from identikit import defaults, engine, features, gitctx
from identikit import discover as discover_mod
from identikit.common import (
    Config,
    ValidationError,
    load_config,
)
from identikit.doctor import check_no_leak
from identikit.marker import MARKER_NAME, marker_exists, write_marker
from identikit.preflight import PreconditionError, check_preconditions

from . import __version__

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Rewrite a live template repo's identity into a new project.",
)

DEFAULT_CONFIG = Path("identikit.toml")
# Paths whose identity values are data, not identity to rewrite/audit.
DOCTOR_EXCLUDES = ("identikit.toml", "identikit", MARKER_NAME)


def _today() -> str:
    return _dt.date.today().isoformat()


def _load(config: Path) -> Config:
    if not config.exists():
        typer.secho(f"config not found: {config}", fg="red", err=True)
        raise typer.Exit(2)
    return load_config(config)


# ── discover ─────────────────────────────────────────────────────────────────


@app.command()
def discover(
    config: Path = typer.Option(DEFAULT_CONFIG, "--config", "-c"),
    output: Path = typer.Option(None, "--output", "-o", help="write TOML to PATH"),
    summary: bool = typer.Option(False, "--summary", help="print occurrence summary"),
    root: Path = typer.Option(Path("."), "--root"),
) -> None:
    """Scan the repo and emit a draft identikit.toml (identity seed from --config)."""
    cfg = _load(config)
    root = root.resolve()
    if summary:
        scan = discover_mod.scan_values(root, cfg.identity, DOCTOR_EXCLUDES)
        typer.echo(discover_mod.summary(scan))
        return
    text = discover_mod.generate(root, cfg.identity, DOCTOR_EXCLUDES)
    if output:
        output.write_text(text, encoding="utf-8")
        typer.secho(f"wrote {output}", fg="green", err=True)
    else:
        typer.echo(text)


# ── init ─────────────────────────────────────────────────────────────────────


def _load_answers_file(path: Path, cfg: Config) -> tuple[dict, dict]:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    answers = raw.get("answers", {})
    missing = [f for f in cfg.identity if f not in answers]
    if missing:
        raise ValueError(f"--answers missing fields: {', '.join(missing)}")
    selections = raw.get("features", {}) or features.default_selections(cfg)
    return answers, selections


def _collect_interactive(cfg: Config, dmap: dict[str, str]) -> dict:
    answers: dict[str, str] = {}
    for name, ident in cfg.identity.items():
        default = dmap.get(name, "")
        label = ident.prompt or name
        answers[name] = typer.prompt(label, default=default).strip()
    return answers


def _collect_features_interactive(cfg: Config) -> dict:
    selections: dict[str, str] = {}
    for name, grp in cfg.features.items():
        label = grp.prompt or f"{name} ({'/'.join(grp.variants)})"
        selections[name] = typer.prompt(
            label, default=grp.default or (grp.variants[0] if grp.variants else "")
        ).strip()
    return selections


@app.command()
def init(
    config: Path = typer.Option(DEFAULT_CONFIG, "--config", "-c"),
    answers: Path = typer.Option(None, "--answers", help="headless answers TOML"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    force: bool = typer.Option(False, "--force"),
    allow_dirty: bool = typer.Option(False, "--allow-dirty"),
    yes: bool = typer.Option(False, "--yes", help="skip the confirm prompt"),
    no_lockfile: bool = typer.Option(False, "--no-lockfile"),
    root: Path = typer.Option(Path("."), "--root"),
) -> None:
    """Rebrand this repo's identity in place (one-shot)."""
    cfg = _load(config)
    root = root.resolve()

    try:
        check_preconditions(
            root, gitctx.git_state(root), force=force, allow_dirty=allow_dirty
        )
    except PreconditionError as e:
        typer.secho(f"init: {e}", fg="red", err=True)
        raise typer.Exit(1) from None

    if answers is not None:
        try:
            ans, selections = _load_answers_file(answers, cfg)
        except (OSError, ValueError, tomllib.TOMLDecodeError) as e:
            typer.secho(f"init: --answers error — {e}", fg="red", err=True)
            raise typer.Exit(1) from None
    else:
        ctx = defaults.context_from_git(
            cfg,
            gitctx.origin_url(root),
            gitctx.user_name(root),
            gitctx.user_email(root),
        )
        ans = _collect_interactive(cfg, defaults.derive_defaults(cfg, ctx))
        selections = _collect_features_interactive(cfg)

    try:
        engine.validate_answers(cfg, ans)
    except (ValidationError, KeyError) as e:
        typer.secho(f"init: invalid answer — {e}", fg="red", err=True)
        raise typer.Exit(1) from None

    plan = engine.build_plan(cfg, ans, root)
    typer.echo(plan.render())
    counts = plan.counts()
    typer.echo(
        f"\nSummary: {counts['remove']} removes, {counts['replace']} replaces, "
        f"{counts['rename']} renames."
    )

    if dry_run:
        typer.echo("\n(--dry-run: no changes written)")
        return

    if not yes and answers is None:
        if not typer.confirm("\nApply these changes?"):
            typer.secho("aborted.", fg="yellow", err=True)
            raise typer.Exit(1)

    run_cfg = dc_replace(cfg, regenerates=()) if no_lockfile else cfg
    try:
        report = engine.apply(run_cfg, ans, root)
    except Exception as e:  # noqa: BLE001 - surface any apply failure with recovery hint
        typer.secho(f"init: APPLY FAILED — {e}", fg="red", err=True)
        typer.secho("recover with: git checkout . && git clean -fd", err=True)
        raise typer.Exit(2) from None

    feat = features.apply_features(cfg, selections, root)
    write_marker(root, ans, version=__version__, date=_today())

    typer.echo(report.render())
    typer.echo(feat.render())
    typer.secho("\n✓ done. Review with `git diff` before committing.", fg="green")


# ── doctor ───────────────────────────────────────────────────────────────────


@app.command()
def doctor(
    config: Path = typer.Option(DEFAULT_CONFIG, "--config", "-c"),
    root: Path = typer.Option(Path("."), "--root"),
) -> None:
    """Audit: fail if any "from" identity value still leaks through the tree."""
    cfg = _load(config)
    report = check_no_leak(cfg, root.resolve(), exclude_paths=DOCTOR_EXCLUDES)
    typer.echo(report.render())
    raise typer.Exit(0 if report.ok() else 1)


# ── prune ────────────────────────────────────────────────────────────────────


@app.command()
def prune(
    config: Path = typer.Option(DEFAULT_CONFIG, "--config", "-c"),
    root: Path = typer.Option(Path("."), "--root"),
    force: bool = typer.Option(False, "--force"),
) -> None:
    """Remove the identikit footprint after a successful init."""
    cfg = _load(config)
    root = root.resolve()
    if not marker_exists(root) and not force:
        typer.secho(
            "prune: marker absent (run init first, or pass --force).",
            fg="red",
            err=True,
        )
        raise typer.Exit(2)
    removed = []
    for rel in cfg.prune:
        target = root / rel
        if not target.exists():
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        removed.append(rel)
    typer.echo(f"pruned: {', '.join(removed) if removed else '(nothing)'}")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"identikit {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    version: bool = typer.Option(
        False,
        "--version",
        help="print version and exit",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Rewrite a live template repo's identity into a new project."""


def main() -> None:
    app()


if __name__ == "__main__":
    main()
