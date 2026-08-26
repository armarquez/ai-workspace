# ollama

Local model tier — the offline fallback when every paid provider is exhausted.

## What actually talks to the network

`ollama pull` is the only command in this module that contacts a remote registry — it downloads
model weights. `ollama serve` and local inference make no outbound calls at all.

That's not a guess: it comes from extracting every `ollama.com`/`ollama.ai` string out of the
exact pinned binary (`ollama --version` reports the version; the binary itself lives under
`~/.local/share/mise/installs/ollama/<version>/ollama`) via `strings`. The only endpoints present
are:

- `/api/web_search` — an explicit, opt-in tool call a model can make, not automatic
- `/api/experimental/model-recommendations` — cloud-model metadata
- `/connect` and `/settings/keys` — `ollama signin`, opt-in, not used by anything in this repo

No `/api/update` or telemetry endpoint exists in this build. (The desktop app — the menubar icon
version, not the CLI binary this repo pins — does have a background update checker; that's a
different artifact and isn't installed here.)

Nothing in `just doctor` or `just bootstrap` calls `just ollama pull` — pulling a model is always
a manual, explicit step.

## The model allowlist

`models.toml`'s `allowed_families` is checked by `just ollama check-model` before every
`just ollama pull`. It exists to stop a typo'd or copy-pasted model name from silently becoming a
`-cloud`-tagged model — those proxy inference to a remote server instead of running locally,
which defeats the entire point of this module. It also means changing which models are in play
shows up as a diff in `models.toml`, not just a bare tag typed into a terminal.

To add a model:

1. Confirm the tag exists at `https://ollama.com/library/<name>/tags` — don't guess a tag from
   memory.
2. Add the family prefix to `allowed_families` if it's new.
3. Add an entry to `[models]` with its size/context noted, so `just ollama check` output stays
   informative.

## Testing a real pull

`just ollama check-model <name>` validates a model name with zero network activity — safe to run
anywhere. A real `just ollama pull` downloads multiple gigabytes from `ollama.com`; if this repo
is also checked out on a work machine, test the actual pull somewhere you're not worried about
generating that traffic from, first.
