default:
    @just --list

# Detect OS for package installation
detect-os:
  #!/usr/bin/env bash
  unameOut="$(uname -s)"
  case "${unameOut}" in
      Linux*)     os=linux;;
      Darwin*)    os=macos;;
      *)          os="unknown"
  esac
  echo "Detected OS: $os"

# 1-Step setup on any new laptop/workstation
bootstrap: up link-configs

# Start background persistent memory gateway
up:
    mkdir -p data
    docker compose up -d

# Link tool configs and rules to current user home
link-configs:
    @echo "Linking agent rules..."
    ln -sf $(pwd)/AGENTS.md $(HOME)/AGENTS.md 2>/dev/null || true
    @echo "Configuring Claude Code..."
    mkdir -p $(HOME)/.claude
    ln -sf $(pwd)/configs/claude.json $(HOME)/.claude.json 2>/dev/null || cp configs/claude.json $(HOME)/.claude.json
    @echo "Setup complete! All CLIs connected to localhost:8000/sse"

# Stop background services
down:
    docker compose down