## Code search: use the graph first

This repo is indexed by codebase-memory-mcp. Prefer its tools over `grep`/`glob` for code structure.

- **Find code:** `search_graph` for functions, classes, and routes by name or meaning.
- **Trace callers and callees:** `trace_path` with `direction` set to `inbound` or `outbound`.
- **Orient in a new area:** `get_architecture`, then `get_code_snippet` for the symbols it names.
- **Check blast radius:** `detect_changes` maps the uncommitted diff to affected symbols.
- **Ensure the graph exists:** call `list_projects` before searching.
  Run `just cbm-ensure` if this checkout or `.codebase-memory/graph.db.zst` is missing.
- **Fall back to grep** for strings, config, comments, and anything dynamic (reflection, dependency injection, generated code). The graph is static, so "no callers" means "no static callers", not "unused".
