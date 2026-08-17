#!/usr/bin/env bash
# Shared host-level checks, run before every provider module's own `check`.
# Never mutates $HOME — only registers the basic-memory project (repo-local
# metadata, not a config file this repo would need to back up).
set -euo pipefail

status=0

# `op whoami` can block indefinitely on a GUI unlock prompt (Touch ID / device
# approval) that never resolves in a non-interactive shell. Bound it manually —
# a portable `timeout` binary isn't guaranteed on every machine this runs on.
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
for tool in mise direnv op uv; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo "  ✓ $tool"
    else
        echo "  ✗ $tool not found — see README for install instructions"
        status=1
    fi
done

echo ""
echo "1Password:"
if ! with_timeout 5 op whoami >/dev/null 2>&1 </dev/null; then
    echo '  ⚠ op not authenticated (or unlock prompt timed out)'
    # shellcheck disable=SC2016 # printed literally for the user to copy, not expanded here
    echo '    run: eval "$(op signin --account my.1password.com)"  (secrets.env uses the Personal vault)'
else
    echo "  ✓ op authenticated"
    while IFS='=' read -r name ref; do
        [ -z "$name" ] && continue
        case "$name" in \#*) continue ;; esac
        if op read "$ref" </dev/null >/dev/null 2>&1; then
            echo "  ✓ $name ($ref)"
        else
            echo "  ⚠ $name not found at $ref — see secrets.env"
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
