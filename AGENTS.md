# ai-workspace

Bootstraps a dev machine with several AI coding CLIs (Claude Code, Antigravity
CLI, opencode, Codex, Ollama), so work can move to another provider when tokens
run low, ending in a fully local fallback.

## Conventions

- **One folder per provider** (`claude/`, `antigravity/`, `opencode/`,
  `codex/`, `ollama/`), each with its own `justfile` surfaced via `mod <name>` in the
  root justfile. Every provider module exposes the same recipes:
  `start`, `check`, `link`, `unlink`. `check` never mutates anything.
- **MCP servers are defined once**, in `mcp/servers.toml`. `scripts/sync-mcp.py`
  renders that into each CLI's native format — never hand-edit `.mcp.json`,
  `.agents/mcp_config.json`, `opencode.json`, or `.codex/config.toml`; they are
  generated and gitignored. Codex's schema is the strict one: `mcp_servers`
  (snake_case) and no `type` key, or the server table fails to deserialize.
- **Toolchain is pinned in `mise.toml`.** Look up current stable versions
  before bumping a pin — do not guess from memory.
- **Secrets come from 1Password** via `op run --env-file=secrets.env`.
  `secrets.env` holds `op://` references only, never a real key. `claude`,
  `codex`, and `antigravity` are exceptions: each signs in with its own
  subscription/account login (`claude login`, ChatGPT, Google), and setting
  the matching API-key env var would override that session and move billing
  to per-token API usage — so their `start` recipes have no `op run` wrapper.
- **Global (`$HOME`) writes are opt-in** via `just link-global` /
  `just <provider> link`, and always back up what they touch. Default
  operation is repo-scoped only.
