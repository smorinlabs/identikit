# identikit

**Rewrite a live template repo's identity into a new project — one-shot, in-place, config-driven.**

`identikit` answers one question — *"how do I turn this template repo into my own project?"* — without
tokenizing the template. A blueprint repo stays a real, runnable, CI-green project (no `{{tokens}}`); its
own identity values (package name, repo name, CLI command, owner, author) act as the "from" side of a
deterministic rewrite. Point `identikit` at a per-repo config and it stamps your project's identity in
place: text replacements, file/dir renames, removals, and lockfile regeneration.

```
$ uvx identikit init
  ⚙  rebrands this template into your project's identity
  one-shot · in-place · no {{tokens}}
```

## Status

Early scaffolding. Design distilled from the `py-launch-blueprint` `init/` self-setup system:
the reusable, identity-agnostic rebrand engine extracted as a standalone `uvx`-runnable tool, driven
by a per-repo config (identity field definitions + a replace/rename/remove/regenerate manifest).

Scope is intentionally **one-shot** (a starting scaffold, not a living standard that keeps tracking its
template), and the rebrand engine is kept separate from any stack-specific service wiring
(publishing/coverage/docs), which belongs in opt-in modules.

## License

MIT (see `LICENSE`).
