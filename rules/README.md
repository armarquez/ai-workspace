# rules

Canonical source for global behavioral guidance and safety hooks — the same role
`mcp/servers.toml` plays for MCP servers.

```
rules/
  master/          committed — the one place this content is authored
    CLAUDE.md        vendored, byte-for-byte, from ~/dotfiles/claude/base/CLAUDE.md
    topics/*.md      vendored, byte-for-byte, from ~/dotfiles/claude/base/rules/*.md
    hooks.toml       the same two PreToolUse guards from ~/dotfiles/claude/base/settings.json,
                     re-authored here since hooks can't be shared by reference across repos
  claude/          generated (gitignored) — never hand-edit
  codex/           generated (gitignored) — never hand-edit
```

`scripts/sync-rules.py render` (`just sync-rules`) renders `rules/master/` into each
agent's own folder:

- **`rules/claude/`** — an identity copy (`CLAUDE.md` + `rules/*.md`), the same shape
  dotfiles' stow puts at `~/.claude`. That stow mechanism stays the real owner of
  `~/.claude` — this render exists so the copy is inspectable and diffable, not to be
  linked anywhere. `just check-rules` proves it still matches the live files.
- **`rules/codex/`** — the same `master/` corpus concatenated into one `AGENTS.md`
  (Codex reads a single global instructions file, not a directory of them) plus
  `hooks.json` — content Codex never had before this. `just codex link` writes this into
  `~/.codex/AGENTS.md` / `~/.codex/hooks.json`, merged inside a marked block so anything
  added there by hand survives a re-link; `just codex unlink` reverses it.

Airbnb-specific rules (`~/dotfiles/claude/airbnb/`) are deliberately **not** vendored
into `rules/master/` — this repo stays free of internal/company references.

```sh
just sync-rules     # write rules/claude/ and rules/codex/ from rules/master/
just check-rules    # read-only: does the render still match live ~/.claude?
just codex link     # writes ~/.codex/AGENTS.md + ~/.codex/hooks.json
just codex unlink   # removes only what this repo added
```
