# ai-workspace

Bootstraps a dev machine to work with several AI coding CLIs, so work can
move to another provider when tokens run low, ending in a fully local
fallback. Everything is pinned in this repo; the host only needs `mise`,
`direnv`, and `op` (1Password CLI).

See [docs/](./docs/README.md) for the architecture, a full recipe reference, and a
walkthrough onboarding another repo onto this toolkit.

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
just codex start           # OpenAI Codex, on a ChatGPT plan
just local                 # opencode + Ollama, fully offline
just squad start           # claude-squad — several of the above in parallel worktrees
```

## Layout

One folder per provider (`claude/`, `antigravity/`, `opencode/`, `codex/`,
`ollama/`), each with its own `justfile` surfaced from the root via
`mod <name>`. Every provider module exposes the same four recipes:

| Recipe | Does |
|---|---|
| `start` | Launch the CLI with secrets injected via `op run`. |
| `check` | Verify install/reachability. Never mutates anything. |
| `link` | Opt-in: merge this repo's MCP servers into the CLI's global (`$HOME`) config, with a backup. |
| `unlink` | Reverse `link`. |

MCP servers are defined once, in `mcp/servers.toml`, and rendered into each
CLI's native format by `scripts/sync-mcp.py` (`just sync-mcp`). Never
hand-edit `.mcp.json`, `.agents/mcp_config.json`, `opencode.json`, or
`.codex/config.toml` — they're generated and gitignored.

| CLI | Repo-scoped config | Root key |
|---|---|---|
| Claude Code | `.mcp.json` | `mcpServers` |
| Antigravity CLI | `.agents/mcp_config.json` | `mcpServers` (remote servers use `serverUrl`) |
| opencode | `opencode.json` | `mcp` |
| Codex | `.codex/config.toml` | `mcp_servers` (TOML; **no** `type` key — see below) |

Two of those have a non-obvious half that is checked in and hand-edited, with
the MCP block appended by the renderer: `opencode/providers.json` for opencode,
and `codex/config-base.toml` for Codex.

Shared instructions live in `AGENTS.md` — opencode and Antigravity read it
natively. Claude Code does not, so `CLAUDE.md` starts with `@AGENTS.md` and
appends Claude-only notes below it. That file documents this repo's own
conventions; it's separate from `rules/`, below, which is personal/global.

Global behavioral guidance and safety hooks live once in `rules/`: `rules/claude/` is a
vendored, byte-for-byte copy of `~/dotfiles/claude/base` (CLAUDE.md + `rules/*.md`) —
the actual files dotfiles' stow puts at `~/.claude`, which stays their owner. Airbnb-
specific rules are deliberately not vendored here. `scripts/sync-rules.py` (`just
sync-rules claude`) drift-checks the vendored copy against the live `~/.claude` files
(read-only), and (`just codex link`) concatenates that same corpus into
`~/.codex/AGENTS.md` + `~/.codex/hooks.json` — content Codex never had before. See
`rules/README.md`.

Shared memory across every CLI is [basic-memory](https://github.com/basicmachines-co/basic-memory) — plain Markdown under
`memory/`, committed like any other file, registered as the `ai-workspace`
project by `just doctor`.

`squad/` runs several of the providers above in parallel via claude-squad — see
[Parallel agents via claude-squad](#parallel-agents-via-claude-squad), below.

`onboard/` brings an *existing* repo onto this toolkit — `CLAUDE.md` → `AGENTS.md`,
agent-CLI tool pins in its `mise.toml`, `basic-memory` in its `.mcp.json` — see
[docs/onboarding-a-repo.md](./docs/onboarding-a-repo.md) for a full walkthrough.

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
- Codex is the one module with no `op run` wrapper, because it authenticates
  with a ChatGPT sign-in (`codex login`) rather than a key. That is deliberate:
  Codex reads `CODEX_API_KEY` from the environment and it *outranks* a stored
  ChatGPT session, so injecting one would silently move billing from the plan to
  per-token API usage. (`OPENAI_API_KEY` is not read for auth at all — only
  `CODEX_API_KEY` is, which is a common source of confusion.)
- Codex asks once whether to trust this directory. Its repo-local config layer
  is inert until you say yes, so `.codex/config.toml` does nothing on the first
  run until you accept the prompt.
- Codex's MCP schema is stricter than the others': the table is `mcp_servers`
  (snake_case), the transport is inferred from `command` vs `url`, and an extra
  key such as `type` is a hard deserialize error that takes the whole server
  table down rather than being ignored. `just codex check` validates the
  rendered file offline for exactly this.
- If `mise install` fails on `ollama` with an extraction error, it's a known
  aqua-backend issue on macOS — fall back to `brew install ollama`.
- Local model tag lives in `ollama/models.toml`; verify any new tag exists at
  `https://ollama.com/library/<name>/tags` before pinning it. See `ollama/README.md` for
  what network calls Ollama actually makes, and why models are checked against an allowlist
  before every pull.
- Codex's sandbox is native-only: an OS-level sandbox (`sandbox_mode`,
  `sandbox_workspace_write.network_access`) plus `shell_environment_policy`'s built-in
  scrubbing of `KEY`/`SECRET`/`TOKEN`-named env vars. It has no credential-masking egress
  proxy like Claude Code's (no `sandbox.credentials`/`injectHosts`/`tlsTerminate`
  equivalent), so a secret in a Codex session's environment reaches whatever host
  `network_access` allows as its real value — a standing difference from the Claude
  sandbox posture managed in `~/dev/anthony-marquez/secret-sandbox-scaffold`, not
  something fixable from `codex/config-base.toml` alone.

## Parallel agents via claude-squad

[claude-squad](https://github.com/smtg-ai/claude-squad) (`squad/`) runs several of the
provider CLIs above in parallel, each in its own tmux session + git worktree — the tooling
behind the `wt switch <branch>` convention already stated in `rules/master/CLAUDE.md`'s
"Parallel subagents require worktrees" rule.

```sh
just squad start   # launches the claude-squad TUI against this repo
```

Inside it, `n`/`N` create a session (with an optional prompt), `↵`/`o` attach, `ctrl-q`
detaches, `s` commits and pushes, `tab` toggles the diff pane. Each new session picks a
profile — `squad/config.json` defines one per provider (`claude`, `codex`, `opencode`,
`antigravity`), each the same command that provider's own `start` recipe runs, minus the
`cd` that recipe does: a claude-squad tmux pane already starts inside its own worktree,
which has its own copy of `secrets.env` since that's a tracked file.

`just squad link` merges those profiles into `~/.claude-squad/config.json` (additive,
backed up first, like every other `link`); `just squad check` verifies `claude-squad`,
`tmux`, and `gh` are installed and that the profiles are present, without mutating anything.

Two things worth knowing before relying on it:

- Each tmux pane's `op run` resolves its own 1Password session. Running several profile
  sessions in parallel can mean several independent auth prompts unless a session token is
  already exported in the shell claude-squad itself launches from (see Secrets, above).
- `gh` is a hard requirement for claude-squad and is now pinned in `mise.toml`, but on this
  machine an Airbnb-forked `gh` earlier in `PATH` still wins — `just squad check` reports
  which one actually resolves. Harmless here (this repo is a personal github.com repo), but
  worth knowing before assuming the pin is authoritative.

## Platform support

Tested on macOS and WSL (Windows Subsystem for Linux) — WSL is real Linux, so every recipe here
works the same as on Linux/macOS. **Bare native Windows (PowerShell/cmd, no WSL) is not
supported**: every multi-line recipe uses a `#!/usr/bin/env bash` shebang, `.envrc`/`direnv`
doesn't work in PowerShell/cmd, and `mise`'s `[env]` block isn't applied on native Windows
outside `mise x`/`mise run`. Fixing that would mean either requiring Git Bash and a
`windows-shell` setting, or rewriting the affected recipes — out of scope for now.

WSL-specific notes:

- `lsof` isn't preinstalled on a fresh WSL Ubuntu image but is needed by `just ollama stop` /
  `just down` — `just doctor` warns if it's missing; fix with `sudo apt-get install lsof`.
- WSL shares the Windows `PATH` by default, so a separately-installed Windows-side binary (most
  likely Ollama's own desktop app) can shadow the WSL/mise-managed one of the same name. `just
  doctor` checks `ollama` specifically and warns if it resolves under `/mnt/`.
- 1Password's biometric desktop-app integration doesn't bridge into WSL — `op signin`/`op run`
  still work, just via typed master password + Secret Key instead of Touch ID/Windows Hello.
- claude-squad itself has no native Windows build; its README points Windows users at WSL,
  consistent with this repo's existing WSL-yes/native-Windows-no stance — no new gap here.
