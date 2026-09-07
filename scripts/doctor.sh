#!/usr/bin/env bash
# Shared host-level checks, run before every provider module's own `check`.
# Never mutates $HOME — only registers the basic-memory project (repo-local
# metadata, not a config file this repo would need to back up).
set -euo pipefail

status=0

# curl/python3 are load-bearing across most recipes (port polling, TOML
# parsing) so a missing one is a hard failure alongside the rest.
# `op` is checked separately below — on WSL the real binary is often
# `op.exe`, reachable via Windows PATH interop, not a Linux `op`.
required_tools=(mise direnv uv curl python3)

# WSL shares the Windows PATH by default, so a Windows-installed 1Password
# CLI shows up here as `op.exe`, not `op`. Prefer `op.exe` when both are
# present — matches infra/ansible/justfile's check-op, and on WSL it's
# usually the one with a real desktop-app integration already set up.
op_cmd() {
    if command -v op.exe >/dev/null 2>&1; then
        echo op.exe
    elif command -v op >/dev/null 2>&1; then
        echo op
    fi
}

# 1Password commands can block indefinitely on a GUI unlock/approval prompt
# that never resolves in a non-interactive shell. Bound them manually — a
# portable `timeout` binary isn't guaranteed on every machine this runs on.
with_timeout() {
    local secs=$1
    shift
    "$@" &
    local pid=$!
    (sleep "$secs" && kill -0 "$pid" 2>/dev/null && kill "$pid" 2>/dev/null) &
    local watcher=$!
    disown "$watcher" 2>/dev/null || true
    if wait "$pid" 2>/dev/null; then
        kill "$watcher" 2>/dev/null || true
        return 0
    else
        kill "$watcher" 2>/dev/null || true
        return 1
    fi
}

echo "Host tools:"
for tool in "${required_tools[@]}"; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo "  ✓ $tool"
    else
        echo "  ✗ $tool not found — see README Quick start for install instructions"
        status=1
    fi
done
OP_CMD=$(op_cmd)
if [ -n "$OP_CMD" ]; then
    if [ "$OP_CMD" = "op.exe" ]; then
        echo "  ✓ op (op.exe via WSL interop)"
    else
        echo "  ✓ op"
    fi
else
    echo "  ✗ op not found — see README Quick start for install instructions"
    status=1
fi
# lsof is only used by `just ollama stop`/`just down`, and isn't preinstalled
# on a fresh WSL Ubuntu image — a soft warning, not a hard failure.
if command -v lsof >/dev/null 2>&1; then
    echo "  ✓ lsof"
else
    echo "  ~ lsof not found — \`just ollama stop\`/\`just down\` won't work (WSL: sudo apt-get install lsof)"
fi
# A fresh machine with direnv + mise installed but never wired together errors with
# "use_mise: command not found" the first time any repo's .envrc runs `use mise`.
if [ -f "$HOME/.config/direnv/lib/use_mise.sh" ] || grep -q "use_mise" "$HOME/.config/direnv/direnvrc" 2>/dev/null; then
    echo "  ✓ direnv's use_mise function is set up"
else
    echo "  ~ direnv's use_mise function missing — \`use mise\` in .envrc will error with"
    echo "    \"use_mise: command not found\" — run: just direnv-setup"
fi

is_wsl() {
    [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qi microsoft /proc/version 2>/dev/null
}
if is_wsl; then
    echo ""
    echo "WSL:"
    ollama_path=$(command -v ollama 2>/dev/null || true)
    case "$ollama_path" in
    /mnt/*)
        echo "  ⚠ ollama resolves to $ollama_path — that's the Windows side, not the mise-managed"
        echo "    Linux binary. WSL shares the Windows PATH by default; a Windows-side Ollama"
        echo "    install can shadow this repo's pinned one. See README § Toolchain notes."
        ;;
    "")
        : # not installed yet — the main tool loop above doesn't cover it, `just ollama check` will
        ;;
    *)
        echo "  ✓ ollama resolves inside WSL ($ollama_path)"
        ;;
    esac
fi

echo ""
echo "1Password:"
if [ -z "$OP_CMD" ]; then
    # Already flagged in the host-tools loop above (status=1) — this just
    # avoids the misleading "not authenticated" message a missing binary
    # would otherwise produce from the whoami call below.
    echo "  ✗ op not installed — see README Quick start for the install command"
elif ! with_timeout 5 "$OP_CMD" account list </dev/null 2>/dev/null | grep -q .; then
    # `account list` (not `whoami`) is the right probe here: `whoami` needs a
    # live CLI session from `op signin`, but desktop-app integration (the
    # normal WSL setup via op.exe) authenticates `read`/`run` per-call via a
    # biometric prompt without ever establishing one — so `whoami` reports
    # "not signed in" even when the account is fully usable.
    echo "  ⚠ $OP_CMD has no accounts configured (or unlock prompt timed out)"
    # shellcheck disable=SC2016 # printed literally for the user to copy, not expanded here
    echo "    run: eval \"\$($OP_CMD signin --account my.1password.com)\"  (secrets.env uses the Personal vault)"
else
    echo "  ✓ $OP_CMD authenticated"
    while IFS='=' read -r name ref; do
        [ -z "$name" ] && continue
        case "$name" in \#*) continue ;; esac
        if with_timeout 5 "$OP_CMD" read "$ref" </dev/null >/dev/null 2>&1; then
            echo "  ✓ $name ($ref)"
        else
            echo "  ⚠ $name not found at $ref, or a desktop-app approval prompt timed out — see secrets.env"
        fi
    done <secrets.env
fi

echo ""
echo "\$HOME conflicts:"
if [ -L "$HOME/.claude/CLAUDE.md" ]; then
    echo "  ✓ ~/.claude is Stow-managed (dotfiles) — this repo will not touch it directly"
fi
if [ -e "$HOME/.claude.json" ] && [ ! -L "$HOME/.claude.json" ]; then
    size=$(wc -c <"$HOME/.claude.json" | tr -d ' ')
    echo "  ✓ ~/.claude.json is a live file (${size} bytes) — link/unlink use \`claude mcp add-json\`, never a rewrite"
fi

echo ""
echo "basic-memory project:"
if command -v basic-memory >/dev/null 2>&1; then
    memory_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/memory"
    if basic-memory project list 2>/dev/null | grep -q "ai-workspace"; then
        echo "  ✓ ai-workspace project registered"
    else
        if basic-memory project add ai-workspace "$memory_dir" >/dev/null 2>&1; then
            echo "  + registered ai-workspace -> $memory_dir"
        else
            echo "  ✗ failed to register ai-workspace project"
            status=1
        fi
    fi
else
    echo "  ✗ basic-memory not found — run: mise install"
    status=1
fi

exit $status
