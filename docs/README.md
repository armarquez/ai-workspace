# Documentation

Start with the root [README.md](../README.md) for the quick start. These go deeper:

- **[architecture.md](./architecture.md)** — why this repo is shaped the way it is: the
  one-source-many-targets render pipeline, and how rules/hooks reach Claude vs. Codex.
- **[recipes.md](./recipes.md)** — every `just` recipe, every module: what it does, when
  to reach for it, the gotchas that don't fit the root README.
- **[conventions.md](./conventions.md)** — the provider contract, the secrets model, the
  `$HOME` write policy, toolchain pinning, and sandbox posture — one section per
  `AGENTS.md`/`CLAUDE.md` bullet, expanded.
- **[onboarding-a-repo.md](./onboarding-a-repo.md)** — a walkthrough: giving a repo that
  doesn't yet use this toolkit its own providers and parallel agent sessions, using
  `infra` as the worked example.
