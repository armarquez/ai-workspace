mod claude
mod antigravity
mod opencode
mod ollama

default:
    @just --list

# One-step setup on any new machine. No $HOME writes — see `link-global`.
bootstrap:
    mise install
    # A freshly-installed tool's shim isn't always resolvable in the same
    # script run as `mise install` (seen on WSL: `prek install` right after
    # bootstrap failed with "not found", worked a moment later). `reshim`
    # makes it available immediately instead of relying on the next shell.
    mise reshim
    just install-hooks
    just sync-mcp
    just doctor

# Install git pre-commit hooks (run once after cloning; safe to re-run) — --overwrite drops any global-template legacy hook
install-hooks:
    prek install --overwrite

# Run pre-commit checks against every file (useful after updating hooks)
lint-all:
    prek run --all-files

# Verify the environment without changing anything
doctor:
    #!/usr/bin/env bash
    set -euo pipefail
    status=0
    bash scripts/doctor.sh || status=1
    echo ""
    just claude check || status=1
    just antigravity check || status=1
    just opencode check || status=1
    just ollama check || status=1
    exit $status

# Render .mcp.json, .agents/mcp_config.json, and opencode.json from mcp/servers.toml
sync-mcp:
    uv run scripts/sync-mcp.py render

# Register this repo's MCP servers in every provider's global ($HOME) config (opt-in; default never leaves this repo)
link-global:
    just claude link
    just antigravity link
    just opencode link
    just ollama link

# Reverse link-global
unlink-global:
    just claude unlink
    just antigravity unlink
    just opencode unlink
    just ollama unlink

# Stop background processes started by this repo's recipes (currently: `ollama serve`)
down:
    just ollama stop

# opencode pinned to the default local model — the offline fallback tier
local:
    #!/usr/bin/env bash
    set -euo pipefail
    model=$(python3 -c "import tomllib; print(tomllib.load(open('ollama/models.toml','rb'))['default'])")
    just ollama serve
    just opencode start "ollama/$model"
