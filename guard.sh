#!/usr/bin/env bash
# identikit reference guard — nudge/block running an un-rebranded template.
#
#   guard.sh warn  <marker_path> <origin_url> [skip_owner/repo ...]  → banner, exit 0
#   guard.sh block <marker_path> <origin_url> [skip_owner/repo ...]  → message, exit 1
#
# Skips (silent, exit 0) when: the marker exists, or the normalized origin
# matches one of the skip patterns (owner/repo — compared as a whole so a fork
# does NOT skip). Pure POSIX-ish bash; no Python, no venv — safe on a bare clone.
#
# This is a *reference* implementation. Wire it into your build tool (just/make/
# npm) per identikit-spec.md §5.4; the skip patterns come from identikit.toml's
# [guard].skip_if_origin.

set -u

mode="${1:-}"
marker="${2:-}"
origin="${3:-}"
shift 3 2>/dev/null || true
skips=("$@")

normalize_origin() {
    printf '%s' "$1" \
        | sed -E 's#^(https?://github\.com/|git@github\.com:)([^/]+)/([^/]+)$#\2/\3#' \
        | sed -E 's#\.git$##'
}

should_skip() {
    [ -n "$marker" ] && [ -f "$marker" ] && return 0
    local norm
    norm="$(normalize_origin "$origin")"
    [ -n "$norm" ] || return 1
    local s
    for s in "${skips[@]:-}"; do
        [ "$norm" = "$s" ] && return 0
    done
    return 1
}

case "$mode" in
    warn)
        if ! should_skip; then
            printf >&2 '\033[33m⚠  template un-initialized — run `identikit init` to re-brand this project.\033[0m\n'
        fi
        exit 0
        ;;
    block)
        should_skip && exit 0
        cat >&2 <<'EOF'

  ───────────────────────────────────────────────────────────────────────
  ⛔  Blocked until this project is initialized.

  This recipe would produce a wrong artifact or external side effect while
  the project still carries the template's identity.

      identikit init     → re-brand this project
      identikit doctor   → diagnose what's missing
  ───────────────────────────────────────────────────────────────────────

EOF
        exit 1
        ;;
    *)
        printf >&2 'guard.sh: unknown mode %s (expected: warn | block)\n' "$mode"
        exit 2
        ;;
esac
