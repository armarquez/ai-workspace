# Recipes

Every `just` recipe in this repo, what it does, and when to reach for it. For the
reasoning behind the patterns below (why `start` always `cd`s first, why `check` never
mutates), see [conventions.md](./conventions.md).

## Root `justfile`

| Recipe | Does |
|---|---|
| `default` | `just --list` — shows this table's recipe names without opening this doc. |
| `bootstrap` | `mise install` → `mise reshim` → `install-hooks` → `sync-mcp` → `sync-rules` → `doctor`. The one command for a new machine. No `$HOME` writes. |
| `install-hooks` | `prek install --overwrite` — git pre-commit hooks. Run once per clone. |
| `lint-all` | `prek run --all-files` — every hook against every file, not just the diff. |
| `doctor` | Runs `scripts/doctor.sh` plus every provider's `check`. Never mutates. Run this whenever something feels off. |
| `sync-mcp` | Renders `.mcp.json`, `.agents/mcp_config.json`, `opencode.json`, `.codex/config.toml` from `mcp/servers.toml`. |
| `sync-rules *args` | Renders `rules/claude/` and `rules/codex/` from `rules/master/`. Repo-local only. Accepts `--input`/`--output` to point at a different pair of folders (used for testing the renderer itself). |
| `check-rules *args` | Read-only: does the render still match live `~/.claude`? Same `--input` override. |
| `link-global` | Runs every provider's `link` — the one command that opts every CLI into global (`$HOME`) registration at once. |
| `unlink-global` | Reverses `link-global`. |
| `down` | Stops background processes this repo's recipes started (today: `ollama serve`). |
| `local` | `ollama serve` + `opencode start` pinned to `ollama/models.toml`'s default — the fully-offline tier. |

## `claude/`, `antigravity/`, `opencode/` — the `op run` providers

These three share a shape: `start` wraps the CLI in `op run --env-file=secrets.env`, so the
real API key exists only in that one child process's environment.

| Recipe | Does |
|---|---|
| `start` | `cd`s to the repo root, then `op run --env-file=secrets.env -- <cli>`. opencode's takes an optional model argument. |
| `check` | Is the binary on `PATH`? Prints its version. Exits 1 if missing. Never mutates. |
| `link` | `sync-mcp.py link <provider>` — merges this repo's MCP servers into that CLI's global config, backed up first. |
| `unlink` | Reverses `link`. |

opencode also has `models` (`opencode models` — lists what's resolvable from the current
provider config, no secrets needed since it's read-only against local config).

## `codex/` — the one without `op run`

Codex authenticates with a ChatGPT sign-in (`codex login`), not an API key, so injecting
`CODEX_API_KEY` would silently move billing from the plan to per-token usage — see
`codex/justfile`'s own header comment. That's why its `start` has no `op run` wrapper.

| Recipe | Does |
|---|---|
| `start model=""` | `cd`s to the repo root, runs `codex` (optionally `--model <model>`). No secrets injected. |
| `exec prompt` | `codex exec '<prompt>'` — one non-interactive turn. |
| `check` | Binary present? Credentials on file (not necessarily *working* — see below)? `.codex/config.toml` valid per `scripts/check-codex-config.py`? Does `~/.codex/AGENTS.md`/`hooks.json` have this repo's managed block? |
| `mcp` | `codex mcp list` — what Codex actually resolves, across global + repo config. |
| `link` | `sync-mcp.py link codex` **and** `sync-rules.py link codex` — MCP servers and rules/hooks together. |
| `unlink` | Reverses both halves of `link`. |

**`codex login status` lies a little.** It reports *credentials on file*, not *credentials
that work*. It can report success while holding an already-spent refresh token — the
failure only shows up on first real use, as *"your refresh token was already used."* Treat
a green `check` as "you've logged in at some point," not "auth is live right now."

## `ollama/` — the local, fully-offline tier

| Recipe | Does |
|---|---|
| `start` | Alias for `serve`. |
| `serve` | Starts `ollama serve` in the background, idempotently — a no-op if it's already up. |
| `stop` | Stops the background server `serve` started. Idempotent. |
| `check-model model` | Validates a model name against `ollama/models.toml`'s `allowed_families` — **no network call**. Rejects anything `-cloud`-tagged (those proxy to a remote server, defeating the point of running locally). |
| `pull model=default_model` | The **only** recipe in this module that makes real network traffic. Runs `check-model` first. |
| `ls` / `ps` / `rm model` | Thin wrappers over `ollama list` / `ollama ps` / `ollama rm`. |
| `check` | Is `ollama` installed? Is it serving? Reports the verified network-call surface (see `ollama/README.md`). |
| `link` / `unlink` | No-ops — Ollama has no global config to register. Present only so every provider module has the same four recipes. |

## `squad/` — parallel agent sessions

Not a model provider; it orchestrates the five above. See
[onboarding-a-repo.md](./onboarding-a-repo.md) for a full walkthrough of using it.

| Recipe | Does |
|---|---|
| `start` | `cd`s to the repo root, then execs `claude-squad`. Launches the TUI against **this** repo specifically — see the gotcha below before pointing it at another one. |
| `check` | Is `claude-squad`/`tmux`/`gh` installed? Does `gh` actually resolve to the mise-managed one, or does something earlier in `PATH` win? Does `~/.claude-squad/config.json` have this repo's profiles? |
| `link` | `sync-squad.py link` — merges `squad/config.json`'s profiles into `~/.claude-squad/config.json` by name, backed up first. |
| `unlink` | Removes only those profile names, leaving anything hand-added untouched. |

## `onboard/` — onboarding a target repo

Not a provider, and not scoped to this repo or `$HOME` like everything else here — every
recipe below takes a `target` path to some *other* repo. See
[onboarding-a-repo.md](./onboarding-a-repo.md) for a full walkthrough.

| Recipe | Does |
|---|---|
| `agents-md target *args` | Converts `target`'s `CLAUDE.md` into `AGENTS.md`, reducing `CLAUDE.md` to `@AGENTS.md`. Aborts if `AGENTS.md` already exists; no-ops if already converted. |
| `mise-tools target *args` | Adds the agent-CLI tool pins `target`'s `mise.toml` is missing (`claude`, `agy`, `opencode`, `codex`, `claude-squad`, `tmux`, `gh`). Never touches a tool `target` already pins at a different version — reports it as a conflict instead. |
| `mcp target *args` | Merges `mcp/servers.toml`'s servers into `target`'s `.mcp.json`. |
| `all target *args` | Runs the three above, in order. |
| `check target` | Read-only status against `target` for all three. Never mutates anything. |

Every recipe except `check` is a dry-run — prints its plan, writes nothing — unless
`*args` includes `--apply`. None of them ever run git in `target`; you review and commit
there yourself. Not added to `just doctor`'s fan-out or `link-global`/`unlink-global` — see
[conventions.md](./conventions.md#onboarding-a-target-repo) for why.

## Gotchas that don't fit a table cell

- **Every `start` recipe `cd`s to the repo root first.** That's correct for launching an
  interactive session against *this* repo, but it's why `squad/config.json`'s profiles
  can't just reuse each provider's `start` command verbatim — a claude-squad tmux pane
  already starts inside its own worktree, and re-`cd`-ing away from it would defeat the
  whole point. Each profile is the same launch command, minus that one `cd`.
- **`secrets.env` travels with every worktree.** It's a tracked file, so `op
  run --env-file=secrets.env` (a *relative* path) still resolves correctly from inside a
  claude-squad worktree of *this* repo — each worktree gets its own copy. It does **not**
  resolve from a worktree of a different repo (like `infra`) — that repo has no
  `secrets.env` of its own. [onboarding-a-repo.md](./onboarding-a-repo.md) covers the fix.
- **`gh` may not resolve to the mise-pinned version.** `squad check` reports this
  explicitly rather than assuming the pin won: a `PATH` entry earlier than mise's shims
  (an Airbnb-forked `gh`, on this machine) can still win. Harmless for a personal
  github.com repo, but worth knowing before assuming the pin is authoritative.
