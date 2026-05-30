"""Derive suggested "to" defaults from git state (spec D2b).

The "from" identity is fixed in config (D2a, invariant across instantiation
modes). The "to" *defaults* that pre-fill the prompts are derived from git, via
each field's ``derive`` rule, with two guards:

  * if origin matches the template's own repo (fork / blueprint), the origin is
    ignored — a fork's origin misreports the new identity;
  * if a derived value collides with that field's own "from" value, it is
    suppressed (empty), so the fork-name collision never auto-fills.

Derive mini-language (the ``derive`` field on an identity field):
  ""                 → no default
  "origin.owner"     → owner parsed from git origin (or "")
  "origin.repo"      → repo parsed from git origin (or "")
  "git.user.name"    → git config user.name
  "git.user.email"   → git config user.email
  "<field>|snake"    → another field's derived value, with '-' → '_'
"""

from __future__ import annotations

from dataclasses import dataclass

from identikit.common import Config, origin_matches, parse_origin


@dataclass(frozen=True)
class DeriveContext:
    origin_owner: str | None
    origin_repo: str | None
    user_name: str
    user_email: str


def context_from_git(
    config: Config, origin_url: str, user_name: str, user_email: str
) -> DeriveContext:
    """Build a derive context, nulling origin when it points at the template."""
    parsed = parse_origin(origin_url)
    if parsed is None or origin_matches(origin_url, config.guard.skip_if_origin):
        return DeriveContext(None, None, user_name, user_email)
    return DeriveContext(parsed[0], parsed[1], user_name, user_email)


def _evaluate(rule: str, ctx: DeriveContext, resolved: dict[str, str]) -> str:
    if not rule:
        return ""
    if rule == "origin.owner":
        return ctx.origin_owner or ""
    if rule == "origin.repo":
        return ctx.origin_repo or ""
    if rule == "git.user.name":
        return ctx.user_name
    if rule == "git.user.email":
        return ctx.user_email
    if "|" in rule:
        ref, _, transform = rule.partition("|")
        base = resolved.get(ref.strip(), "")
        if transform.strip() == "snake":
            return base.replace("-", "_")
        return base
    return ""


def derive_defaults(config: Config, ctx: DeriveContext) -> dict[str, str]:
    """Suggested default per identity field; "" when nothing safe to suggest.

    Fields may reference each other (``package_name = repo_name|snake``), so we
    iterate to a fixpoint — order in the config does not matter for resolution.
    """
    resolved: dict[str, str] = dict.fromkeys(config.identity, "")
    for _ in range(len(config.identity)):
        changed = False
        for name, ident in config.identity.items():
            value = _evaluate(ident.derive, ctx, resolved)
            # Collision guard: never suggest the field's own FROM value (D2b, fork).
            if value == ident.value:
                value = ""
            if value != resolved[name]:
                resolved[name] = value
                changed = True
        if not changed:
            break
    return resolved
