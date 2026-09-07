# Walkthrough: giving `infra` the rest of the toolkit

A concrete example, using `~/dev/armarquez/infra` — a real, already-in-use repo — as the
subject. Nothing here is infra-specific advice; swap in any other repo's path.

## What infra already has, and what this adds

`infra` isn't starting from zero. Its most recent commit is *"Add secret key architecture
doc and agent sandbox policy"* — it already has its own `mise.toml`, `direnv`, `CLAUDE.md`,
a `.claude/` sandbox policy, and its own `secrets.env` (own vault refs, resolved by its own
`scripts/agent-session.sh` wrapper — a separate scaffold, unrelated to ai-workspace's
`secrets.env`). It already works with Claude Code, on its own.

| | infra already has | ai-workspace adds |
|---|---|---|
| Claude Code | ✓ own toolchain, own sandbox policy | — |
| `secrets.env` (op:// refs, no real secrets) | ✓ own vault, own `agent-session.sh` wrapper — currently empty of refs | the `OPENROUTER_API_KEY` ref opencode needs, appended by hand — see Step 2. Codex and Antigravity need nothing here — they authenticate with their own login |
| Codex, opencode, Antigravity | ✗ | ✓ |
| Parallel agent sessions | ✗ | ✓ (claude-squad) |
| `AGENTS.md` (generic, non-Claude-specific instructions) | ✗ | ✓ (`just onboard agents-md`) |
| Agent-CLI tool pins in `mise.toml` | ✗ | ✓ (`just onboard mise-tools`) |
| `basic-memory` in `.mcp.json` | ✗ | ✓ (`just onboard mcp`) |

So this walkthrough's job is narrow: give `infra` the providers it doesn't have, the
generic-instructions file other providers read natively, the one op:// ref opencode needs
in infra's own `secrets.env`, and the ability to run several providers at once, each in
its own worktree.

## Prerequisite

ai-workspace itself is bootstrapped once, from *this* repo:

```sh
mise trust && mise install
just bootstrap
```

If `just doctor` is clean (or the only warnings are "not yet linked," which is expected —
linking is opt-in), the prerequisite is met. This is the one step that happens in
ai-workspace's own directory; everything below happens from `infra`'s.

## Step 1 — the mechanical setup: AGENTS.md, mise.toml, .mcp.json

`onboard/` (see [recipes.md](./recipes.md#onboard--onboarding-a-target-repo)) automates the
three pieces that don't need a human judgment call. Every command below is a dry-run —
prints its plan, writes nothing — unless `--apply` is passed:

```sh
just onboard check ~/dev/armarquez/infra          # read-only status first
just onboard all ~/dev/armarquez/infra            # dry-run plan
just onboard all ~/dev/armarquez/infra --apply    # write it
```

This converts `infra`'s `CLAUDE.md` into `AGENTS.md` (with `CLAUDE.md` reduced to
`@AGENTS.md`), adds the agent-CLI tool pins from ai-workspace's own `mise.toml` that
`infra` is missing, and merges `basic-memory` into `infra`'s `.mcp.json`. It never runs
git in `infra` — review the diff and commit it there yourself, the normal way. See
[conventions.md](./conventions.md#onboarding-a-target-repo) for the full safety model,
including how a version conflict (an agent-CLI tool `infra` already pins at a different
version) is reported, never silently resolved.

## Step 2 — one extra agent on infra

Codex and Antigravity need nothing here — like `claude` (which infra already runs, via
its own `agent-session.sh`), both authenticate with their own subscription/account login,
not an `op://` secret, so they just run directly:

```sh
cd ~/dev/armarquez/infra
codex
agy
```

**opencode is the exception** — it authenticates via OpenRouter, a real API key with no
subscription alternative, so it needs the `OPENROUTER_API_KEY` op:// ref ai-workspace's
own `secrets.env` defines. Which path to take depends on whether the target repo already
has a `secrets.env` of its own — two different situations, both covered below.

**If the target has no `secrets.env` at all**, there's nothing local to add the ref to, so
point `op run` at ai-workspace's absolute path instead:

```sh
cd ~/dev/armarquez/some-other-repo
op run --env-file=~/dev/armarquez/ai-workspace/secrets.env -- opencode
```

**`infra` already has its own `secrets.env`** (added by a separate scaffold, for infra's
own secrets — see the table above), just not this ref yet. Append it there instead of
reaching for an absolute path:

```sh
# infra/secrets.env
OPENROUTER_API_KEY=op://Personal/OpenRouter API/credential
```

Then run with a plain relative path, same as ai-workspace's own `opencode/justfile` does:

```sh
cd ~/dev/armarquez/infra
op run --env-file=secrets.env -- opencode
```

**Caveat:** infra's own `scripts/agent-session.sh` wrapper only launches `claude`, with a
`--settings .claude/sandbox-policy.json` flag that's Claude-specific. Codex, opencode, and
Antigravity above all bypass that wrapper — and its sandbox policy — entirely. Extending
the wrapper to cover them is a separate, infra-specific change; this walkthrough doesn't do
it for you.

## Step 3 — parallel agents on infra via claude-squad

`just squad start` won't work here — it's scoped to ai-workspace's own root (see the
gotcha in [recipes.md](./recipes.md)). Run the binary directly from `infra`'s directory
instead:

```sh
cd ~/dev/armarquez/infra
claude-squad
```

**One adjustment first — and only for the `opencode` profile.** `claude`, `codex`, and
`antigravity` need no secrets, so their profiles run the same everywhere, unchanged.
`opencode`'s profile points at a *relative* `secrets.env`, which resolves correctly inside
an ai-workspace worktree (every worktree gets its own copy, since it's a tracked file) —
and, once Step 2's ref is appended to `infra/secrets.env`, resolves just as correctly
inside an `infra` worktree too, since that file is tracked there as well. Open
`~/.claude-squad/config.json` and copy `infra`'s profiles over verbatim:

```json
{
  "profiles": [
    { "name": "claude", "program": "claude" },
    { "name": "codex", "program": "codex" },
    { "name": "opencode", "program": "op run --env-file=secrets.env -- opencode" },
    { "name": "antigravity", "program": "agy" }
  ]
}
```

Only reach for an absolute path on `opencode`'s profile if the target genuinely has no
`secrets.env` of its own (see Step 2's other case):

```json
{ "name": "opencode", "program": "op run --env-file=/Users/you/dev/armarquez/ai-workspace/secrets.env -- opencode" }
```

This is a per-target-repo edit, made once, by hand — not something `just squad link`
should guess at, since it has no way to know which repo you'll point claude-squad at next.

## Step 4 — a worked example: two agents, two worktrees

```mermaid
flowchart LR
    H[You] -->|"n, pick a profile"| CS[claude-squad]
    CS --> W1["Worktree A<br />(claude session)"]
    CS --> W2["Worktree B<br />(codex session)"]
    W1 -->|"s: commit + push"| B1[branch A]
    W2 -->|"s: commit + push"| B2[branch B]
    B1 --> PR[Pull request]
    B2 --> PR
```

1. `n` — new session, pick the `claude` profile, give it a task.
2. `n` again — new session, pick `codex`, give it a different task. claude-squad now has
   two sessions, each in its own worktree, each on its own branch.
3. `tab` toggles between the session's live output and a diff of its worktree — review
   either without leaving the TUI.
4. `↵`/`o` attaches to a session to reprompt it directly; `ctrl-q` detaches back to the
   list.
5. `s` commits and pushes a session's branch, once you're happy with it. Open the PR the
   normal way from there.

## Caveats

- **`PATH` may not resolve what you expect.** A clean shell test (a login shell with no
  inherited state) found `claude`/`codex` resolving to unrelated `/usr/local/bin` installs
  and `gh` resolving to a machine-specific fork — none of them the mise-pinned versions.
  `just squad check` (run from ai-workspace) reports the `gh` case explicitly; the same
  risk applies to any CLI you invoke directly rather than through a `just <provider>
  start` recipe. If a command isn't behaving like the pinned version, run `which <cli>`
  first.
- **`op run`'s session cache is per-shell.** Only the `opencode` profile touches it, but
  running several `opencode` sessions in parallel can still mean several independent
  1Password prompts, unless a session token is already exported in the shell claude-squad
  itself launches from (see [conventions.md](./conventions.md#the-secrets-model)).
- **Two different sandbox postures are now in play.** `infra`'s own `.claude/` policy
  covers Claude Code sessions on it. Codex sessions on the same repo fall back to
  ai-workspace's native-only Codex sandbox (`codex/config-base.toml`) — no
  credential-masking egress proxy, so a secret in a Codex session's environment reaches
  whatever host `network_access` allows, as its real value. See
  [conventions.md](./conventions.md#sandbox-posture) for the full comparison. Nothing
  here extends `infra`'s own Claude sandbox policy to Codex — that would need its own,
  separate design.
