# Conventions

`AGENTS.md` and `CLAUDE.md` state these as one-line rules, for an agent that re-reads them
every session. This is the same content, expanded for a human reading it once. Each
section links back to the file that actually enforces it.

## The provider module contract

Every module under `claude/`, `antigravity/`, `opencode/`, `codex/`, `ollama/`, `squad/`
exposes the same four recipes. Each one means the same thing everywhere:

- **`start`** — launch the CLI, with secrets injected where that CLI needs them.
- **`check`** — verify install and reachability. **Never mutates anything.** This is the
  one every other recipe (and `just doctor`) can call freely without side effects, so it's
  also the one you reach for first when something feels wrong.
- **`link`** — opt-in: register this repo's config in that CLI's global (`$HOME`) config.
  Additive, always backed up first.
- **`unlink`** — reverse `link`.

`squad/` follows the same shape even though it isn't a model provider (see
[architecture.md](./architecture.md#the-provider-module-contract)) — consistency here
means `just doctor` and `just link-global` can treat all six modules identically, with no
special case.

## The secrets model

`secrets.env` (repo root) holds only `op://` references — safe to commit, never a real
key. `opencode`'s `start` resolves them at launch via:

```sh
op run --env-file=secrets.env -- <cli>
```

This injects real values into that **one child process's** environment only. They're
never written to disk, and a sibling process can't read them off `op run`'s own
invocation.

`op run` itself needs to authenticate to 1Password first — once per terminal, via `eval
"$(op signin --account my.1password.com)"` (see the root README's Secrets section for why
`--account` is needed on this machine). That authentication is cached in the shell's
environment for about 30 minutes, not on disk — every `start` in that terminal reuses it
silently; a new terminal, or one that's timed out, needs it again. `just doctor` checks
this and tells you if it's stale.

**`claude`, `codex`, and `antigravity` are the deliberate exceptions.** `claude` and
`codex` authenticate with their own subscription login (`claude login`, a ChatGPT sign-in
via `codex login`), and the matching API-key env var (`ANTHROPIC_API_KEY`,
`CODEX_API_KEY`) *outranks* a stored login session — injecting one via `op run` would
silently move billing from the plan to per-token API usage. `antigravity` (`agy`)
authenticates with its own Google sign-in and reads neither secret at all, so wrapping it
would only add a pointless dependency on 1Password resolving successfully. None of their
`start` recipes have an `op run` wrapper. See each justfile's header comment for the full
reasoning.

## The `$HOME` write policy

Default operation never writes outside this repo — `bootstrap` and `sync-*` are
repo-local only. Writing to `$HOME` is always something you opt into, one of two ways:

- `just link-global` — every provider's `link` at once.
- `just <provider> link` — one provider.

And every `link`, everywhere, follows the same two rules:

1. **Additive, never a wholesale rewrite.** Claude Code goes through `claude mcp add-json
   ... -s user`, which merges into `~/.claude.json` — never a symlink, never an overwrite.
   Everything else does a JSON- or marker-delimited merge (`scripts/sync-mcp.py`,
   `scripts/sync-rules.py`, `scripts/sync-squad.py` all share this shape: read what's
   there, replace only the keys/entries this repo owns, write it back).
2. **Backed up first.** Every one of those scripts calls a `backup()` that timestamps a
   `.bak` copy before touching an existing file — `*.bak`/`*.*.bak` are gitignored on
   purpose, they're a local safety net, not something meant to be committed.

`unlink` reverses `link` by removing only what this repo added — a hand-edited profile,
hook, or MCP server sitting alongside it survives.

## Toolchain pinning philosophy

Every tool version lives in `mise.toml`'s `[tools]` table, not on the host. The host only
ever needs `mise`, `direnv`, and `op` — `mise install` handles everything else, pinned.

When a pin needs bumping, the version is looked up fresh (`mise ls-remote <tool>`, or the
tool's own releases page) — never guessed from memory. `mise.toml`'s own header comment
says this outright, and it's why every line in that file carries a link to where its
version came from.

## Rules and hooks

`rules/master/` is the one place global behavioral guidance and safety hooks are
authored. What happens to it per agent is asymmetric on purpose — see
[architecture.md](./architecture.md#rules-and-hooks-claude-vs-codex) for why. Day to day:

- `just check-rules` — read-only, proves the vendored copy still matches live `~/.claude`.
  Run this after changing anything in `~/dotfiles/claude/base`.
- `just codex link` — writes `~/.codex/AGENTS.md` and `~/.codex/hooks.json`, each inside a
  marked block (`<!-- BEGIN ai-workspace rules -->` / `<!-- END -->` for the former, a
  `# ai-workspace:<id>` comment per hook command for the latter), so anything you add by
  hand outside those markers survives a re-`link`.

## Onboarding a target repo

`onboard/` (see [recipes.md](./recipes.md#onboard--onboarding-a-target-repo)) is the one
part of this repo that writes into an arbitrary third-party repo instead of this repo or
`$HOME` — a higher blast radius than anything else here, since the target is someone's
real, live repo. Two guardrails beyond the usual backup-first convention:

- **Dry-run by default.** Every mutating command prints its plan and writes nothing unless
  `--apply` is passed.
- **Never runs git in the target repo.** No `git add`/`commit`/`push` there — the script
  only edits files on disk; the user reviews and commits them in that repo's own workflow.

The `mise.toml` merge is additive-only in the same sense as everything else `link` does:
a tool already pinned in the target at a version that disagrees with this repo's own pin
is reported as a conflict and left alone, never silently overridden. See
[onboarding-a-repo.md](./onboarding-a-repo.md) for the full walkthrough.

## Sandbox posture

Codex's sandbox here is native-only: an OS-level sandbox (`sandbox_mode`,
`sandbox_workspace_write.network_access`) plus `shell_environment_policy`'s built-in
scrubbing of `KEY`/`SECRET`/`TOKEN`-named env vars — both pinned explicitly in
`codex/config-base.toml` rather than trusted to Codex's own defaults. It has **no**
credential-masking egress proxy like Claude Code's (no `sandbox.credentials` /
`injectHosts` / `tlsTerminate` equivalent). A secret in a Codex session's environment
reaches whatever host `network_access` allows, as its real value —
`codex/config-base.toml` states this plainly rather than leaving it to be discovered
later. See
[onboarding-a-repo.md](./onboarding-a-repo.md#caveats) for how this compares to a target
repo that already has its own Claude Code sandbox policy.
