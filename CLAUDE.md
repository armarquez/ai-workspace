@AGENTS.md

## Claude-Code-specific

- This repo's `claude/justfile` module is unrelated to `~/dotfiles/claude/justfile`
  — the latter manages your global `~/.claude` config via Stow; this one only
  ever touches this repo or, when explicitly asked, registers MCP servers via
  `claude mcp add-json ... -s user` (never a symlink or file overwrite).
