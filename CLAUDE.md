@AGENTS.md

## Claude-Code-specific

- This repo's `claude/justfile` module is unrelated to `~/dotfiles/claude/justfile`
  — the latter manages your global `~/.claude` config via Stow; this one only
  ever touches this repo or, when explicitly asked, registers MCP servers via
  `claude mcp add-json ... -s user` (never a symlink or file overwrite).

## WSL: `op` vs `op.exe`

This repo is developed on both macOS and WSL. On WSL, the 1Password CLI usually isn't
a Linux `op` — it's the Windows-side `op.exe`, reachable via WSL's shared `PATH`, which
also carries the desktop app's biometric integration. Any new code that shells out to
`op` directly (a justfile recipe, a `squad/config.json` profile, a script) needs the
same `op`/`op.exe` resolution, not a bare `op` call — see `scripts/doctor.sh`'s
`op_cmd()` for the canonical version, and README § WSL-specific notes for the full
rationale (`account list` vs `whoami` for the auth check, why `op.exe` is preferred
when both are present). This has already bitten one contributor: `squad/config.json`'s
profiles shipped with bare `op run ...` strings that fail on WSL.
