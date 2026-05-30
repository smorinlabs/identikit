"""Structured rewriters — format-preserving edits for files where blind text
replacement is too blunt.

For TOML, ``rewrite_structured`` walks the parsed document with tomlkit and
replaces the identity value only inside *string values*, leaving comments and
key names untouched. That is the difference from text mode: a comment carrying a
historical/annotation occurrence (e.g. ``# ITM-026 …``) is preserved, and the
document's formatting survives the round-trip.

Any non-TOML file routed here falls back to plain text replacement, so the
manifest can mark a file ``structured`` without identikit needing a dedicated
rewriter for every format yet.
"""

from __future__ import annotations

from pathlib import Path


def _replace_in_container(container: object, src: str, dst: str) -> bool:
    """Recursively replace ``src``→``dst`` in string values of a tomlkit node."""
    changed = False
    if isinstance(container, dict):
        for key in list(container.keys()):
            value = container[key]
            if isinstance(value, (dict, list)):
                changed |= _replace_in_container(value, src, dst)
            elif isinstance(value, str) and src in value:
                container[key] = value.replace(src, dst)
                changed = True
    elif isinstance(container, list):
        for i, value in enumerate(container):
            if isinstance(value, (dict, list)):
                changed |= _replace_in_container(value, src, dst)
            elif isinstance(value, str) and src in value:
                container[i] = value.replace(src, dst)
                changed = True
    return changed


def _rewrite_toml(path: Path, src: str, dst: str) -> bool:
    import tomlkit

    doc = tomlkit.parse(path.read_text(encoding="utf-8"))
    if not _replace_in_container(doc, src, dst):
        return False
    path.write_text(tomlkit.dumps(doc), encoding="utf-8")
    return True


def _rewrite_text(path: Path, src: str, dst: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if src not in text or src == dst:
        return False
    path.write_text(text.replace(src, dst), encoding="utf-8")
    return True


def rewrite_structured(path: Path, src: str, dst: str) -> bool:
    """Replace ``src``→``dst`` in ``path``; True iff the file changed.

    TOML files get a tomlkit value-only edit; everything else falls back to text.
    """
    if path.suffix == ".toml":
        return _rewrite_toml(path, src, dst)
    return _rewrite_text(path, src, dst)
