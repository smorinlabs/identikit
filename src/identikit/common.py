"""Shared config model, validators, and origin parsing for identikit.

The single source of truth for an identikit run is one ``identikit.toml`` file
(see identikit-spec.md §5.2). This module loads it into a typed, field-agnostic
``Config``: identity is a *map* of field name → IdentityField, never a fixed set
of named fields — that is what makes the engine reusable across stacks.

Stdlib-only (tomllib) so the config can be read on a bare clone before any
third-party deps are installed.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

# ── validators ───────────────────────────────────────────────────────────────

PYTHON_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")
REPO_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
COMMAND_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
# GitHub: 1-39 chars, alphanumeric + hyphen, not starting/ending with a hyphen.
GITHUB_OWNER_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,37}[a-z0-9])?$", re.IGNORECASE)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(ValueError):
    """Raised when a user-supplied answer fails its field validator."""


def _make_regex_validator(name: str, pattern: re.Pattern[str], hint: str):
    def _validate(value: str) -> str:
        if not pattern.fullmatch(value):
            raise ValidationError(f"{name} must be {hint}: {value!r}")
        return value

    return _validate


VALIDATORS: dict[str, Callable[[str], str]] = {
    "python_identifier": _make_regex_validator(
        "package name", PYTHON_IDENTIFIER_RE, "a lowercase Python identifier"
    ),
    "repo_name": _make_regex_validator(
        "repo name", REPO_NAME_RE, "lowercase alphanumeric + hyphens"
    ),
    "command_name": _make_regex_validator(
        "command name", COMMAND_NAME_RE, "lowercase alphanumeric + hyphens"
    ),
    "github_owner": _make_regex_validator(
        "GitHub owner", GITHUB_OWNER_RE, "1-39 chars, alphanumeric + interior hyphens"
    ),
    "email": _make_regex_validator("email", EMAIL_RE, "local@domain.tld"),
}


def validate_value(validator_name: str, value: str) -> str:
    """Validate ``value`` against a named validator.

    An empty or unknown validator name is a no-op pass-through — that is how
    free-text identity fields (author name, description) opt out of validation.
    """
    validator = VALIDATORS.get(validator_name)
    if validator is None:
        return value
    return validator(value)


# ── origin parsing ───────────────────────────────────────────────────────────

_ORIGIN_RE = re.compile(
    r"^(?:https?://github\.com/|git@github\.com:)"
    r"(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$"
)


def parse_origin(url: str) -> tuple[str, str] | None:
    """Normalize a GitHub origin URL to ``(owner, repo)`` or ``None``.

    Handles HTTPS and SSH forms, with or without a trailing ``.git``.
    """
    m = _ORIGIN_RE.match(url.strip())
    return (m["owner"], m["repo"]) if m else None


def origin_matches(url: str, patterns: tuple[str, ...]) -> bool:
    """True if ``url`` resolves to one of the ``owner/repo`` skip patterns.

    Compares owner AND repo, never name alone — so a fork (same repo name,
    different owner) does not match (spec §7, instantiation mode 4).
    """
    parsed = parse_origin(url)
    if parsed is None:
        return False
    return f"{parsed[0]}/{parsed[1]}" in patterns


# ── config model ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class IdentityField:
    """One identity field: its current ("from") value and prompt metadata."""

    name: str
    value: str
    validate: str = ""
    prompt: str = ""
    derive: str = ""


@dataclass(frozen=True)
class ReplaceOp:
    field: str
    files: tuple[str, ...]
    mode: str  # "structured" | "text"


@dataclass(frozen=True)
class RenameOp:
    src: str  # may contain {field} templates in dst
    dst: str


@dataclass(frozen=True)
class RemoveOp:
    path: str
    reason: str = ""


@dataclass(frozen=True)
class RegenerateOp:
    path: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class FeatureGroup:
    """A `toggle` group:variant set the project creator selects at init time."""

    name: str
    variants: tuple[str, ...]
    prompt: str = ""
    default: str = ""


@dataclass(frozen=True)
class GuardConfig:
    skip_if_origin: tuple[str, ...] = ()
    block: tuple[str, ...] = ()


@dataclass(frozen=True)
class Config:
    identity: dict[str, IdentityField] = field(default_factory=dict)
    replaces: tuple[ReplaceOp, ...] = ()
    renames: tuple[RenameOp, ...] = ()
    removes: tuple[RemoveOp, ...] = ()
    regenerates: tuple[RegenerateOp, ...] = ()
    features: dict[str, FeatureGroup] = field(default_factory=dict)
    guard: GuardConfig = field(default_factory=GuardConfig)
    prune: tuple[str, ...] = ()

    def from_values(self) -> dict[str, str]:
        """Map of field name → its current ("from") value."""
        return {name: f.value for name, f in self.identity.items()}


def load_config(path: Path) -> Config:
    """Parse an ``identikit.toml`` into a typed, field-agnostic ``Config``."""
    raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))

    identity = {
        name: IdentityField(
            name=name,
            value=spec["value"],
            validate=spec.get("validate", ""),
            prompt=spec.get("prompt", ""),
            derive=spec.get("derive", ""),
        )
        for name, spec in raw.get("identity", {}).items()
    }

    features = {
        name: FeatureGroup(
            name=name,
            variants=tuple(spec.get("variants", ())),
            prompt=spec.get("prompt", ""),
            default=spec.get("default", ""),
        )
        for name, spec in raw.get("features", {}).items()
    }

    guard_raw = raw.get("guard", {})
    guard = GuardConfig(
        skip_if_origin=tuple(guard_raw.get("skip_if_origin", ())),
        block=tuple(guard_raw.get("block", ())),
    )

    return Config(
        identity=identity,
        replaces=tuple(
            ReplaceOp(
                field=r["field"],
                files=tuple(r.get("files", ())),
                mode=r.get("mode", "text"),
            )
            for r in raw.get("replace", [])
        ),
        renames=tuple(
            RenameOp(src=r["from"], dst=r["to"]) for r in raw.get("rename", [])
        ),
        removes=tuple(
            RemoveOp(path=r["path"], reason=r.get("reason", ""))
            for r in raw.get("remove", [])
        ),
        regenerates=tuple(
            RegenerateOp(path=r["path"], command=tuple(r["command"]))
            for r in raw.get("regenerate", [])
        ),
        features=features,
        guard=guard,
        prune=tuple(raw.get("prune", {}).get("paths", ())),
    )
