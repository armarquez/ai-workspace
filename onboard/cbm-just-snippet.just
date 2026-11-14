# BEGIN ai-workspace codebase-memory
# Ensure this checkout has a local graph and a team-shared graph artifact.
cbm-ensure:
    #!/usr/bin/env bash
    set -euo pipefail
    repo_root="$(git rev-parse --show-toplevel)"
    repo_name="$(basename "$repo_root")"
    remote_url="$(git remote get-url origin 2>/dev/null || true)"
    if [[ -n "$remote_url" ]]; then
      repo_name="$(basename "$remote_url" .git)"
    fi
    projects="$(codebase-memory-mcp cli --json list_projects)"
    artifact="$repo_root/.codebase-memory/graph.db.zst"

    if [[ "$projects" == *"$repo_root"* && -f "$artifact" ]]; then
      echo "codebase-memory graph and shared artifact are ready"
      exit 0
    fi

    codebase-memory-mcp cli --progress index_repository \
      --repo-path "$repo_root" \
      --name "$repo_name" \
      --persistence true
# END ai-workspace codebase-memory
