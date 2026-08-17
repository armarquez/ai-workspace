# ai-workspace

Bootstraps a dev machine to work with several AI coding CLIs, so work can
move to another provider when tokens run low, ending in a fully local
fallback. Everything is pinned in this repo; the host only needs `mise`,
`direnv`, and `op` (1Password CLI).

## Quick start

```sh
mise trust && mise install
just bootstrap   # mise install + sync-mcp + doctor — no $HOME writes
```

Then pick a tier:

```sh
just claude start          # subscription, primary driver
just antigravity start     # agy — Google's replacement for the retired Gemini CLI
just opencode start        # OpenRouter spillover, or any of its 75+ providers
just local                 # opencode + Ollama, fully offline
```

## Layout

One folder per provider (`claude/`, `antigravity/`, `opencode/`, `ollama/`),
each with its own `justfile` surfaced from the root via `mod <name>`. Every
provider module exposes the same four recipes:

| Recipe | Does |
|---|---|
| `start` | Launch the CLI with secrets injected via `op run`. |
| `check` | Verify install/reachability. Never mutates anything. |
| `link` | Opt-in: merge this repo's MCP servers into the CLI's global (`$HOME`) config, with a backup. |
| `unlink` | Reverse `link`. |

MCP servers are defined once, in `mcp/servers.toml`, and rendered into each
CLI's native format by `scripts/sync-mcp.py` (`just sync-mcp`). Never
hand-edit `.mcp.json`, `.agents/mcp_config.json`, or `opencode.json` — they're
generated and gitignored.

| CLI | Repo-scoped config | Root key |
|---|---|---|
| Claude Code | `.mcp.json` | `mcpServers` |
| Antigravity CLI | `.agents/mcp_config.json` | `mcpServers` (remote servers use `serverUrl`) |
| opencode | `opencode.json` | `mcp` |

Shared instructions live in `AGENTS.md` — opencode and Antigravity read it
natively. Claude Code does not, so `CLAUDE.md` starts with `@AGENTS.md` and
appends Claude-only notes below it.

Shared memory across every CLI is [basic-memory](https://github.com/basicmachines-co/basic-memory) — plain Markdown under
`memory/`, committed like any other file, registered as the `ai-workspace`
project by `just doctor`.

## Secrets

`secrets.env` holds only `op://` references (safe to commit); each `start`
recipe resolves them at launch via `op run --env-file=secrets.env -- <cmd>`,
which injects the real values into that one child process's environment and
never writes them to disk.

`op run` itself still needs to authenticate to 1Password to resolve those
references. Once per terminal session, run:

```sh
eval "$(op signin --account my.1password.com)"
```

(`secrets.env` points at the `Personal` vault, i.e. the `my.1password.com`
account — if you only have one 1Password account, `--account` isn't needed;
this machine has both a personal and an Airbnb account, so `op signin` alone
fails with "multiple accounts found.")

This caches a session token in that shell's environment (not on disk) for
about 30 minutes, so every `just <provider> start` in that terminal reuses it
without a repeat prompt. A new terminal — or a session that's timed out —
needs it again. `just doctor` checks this and tells you if it's stale.

## A note on `$HOME`

Default operation never writes outside this repo. `just link-global` (or a
single provider's `just <provider> link`) opts in to also registering
servers globally, always additively:

- Claude Code: `claude mcp add-json ... -s user`, which merges into
  `~/.claude.json` — never a symlink or rewrite of that file.
- Antigravity / opencode: a `jq`-style merge into their global config, with
  a timestamped backup first.

**If you also use `~/dotfiles`** (Stow-managed `~/.claude`): this repo's
`claude/justfile` module is unrelated to `~/dotfiles/claude/justfile` — same
name, different repo, different job. Neither one touches
`~/.claude/settings.json` or `~/.claude/rules/`; those stay owned by Stow and
`just claude gen-settings` in `~/dotfiles`.

## Toolchain notes

- `just` here is pinned to `1.58.0`; `~/dotfiles` pins `1.53.0`. `mise`
  scopes per-directory, so this is expected, not a bug.
- Claude Code self-updates its binary; `DISABLE_AUTOUPDATER=1` in
  `mise.toml`'s `[env]` keeps the pin meaningful past the first install.
- If `mise install` fails on `ollama` with an extraction error, it's a known
  aqua-backend issue on macOS — fall back to `brew install ollama`.
- Local model tag lives in `ollama/models.toml`; verify any new tag exists at
  `https://ollama.com/library/<name>/tags` before pinning it. See `ollama/README.md` for
  what network calls Ollama actually makes, and why models are checked against an allowlist
  before every pull.
