#!/usr/bin/env python3
"""Validate a rendered Codex config offline.

Used by `just codex check`. Deliberately does not shell out to `codex`:
`codex mcp list` needs working auth, and `codex exec --strict-config` would
spend a real model turn — neither belongs in a `check` recipe.

What it catches is the failure mode specific to Codex's MCP schema. The
transport is an untagged serde enum with deny_unknown_fields, so:

  - it is `mcp_servers`, never `mcpServers`
  - transport is inferred structurally: `command` => stdio, `url` => http
  - an extra key such as `type` is a hard deserialize error, not an ignored
    field, and it takes the whole server table down with it

https://developers.openai.com/codex/mcp
"""

import sys
from pathlib import Path

import tomllib

# From McpServerTransportConfig + the McpServerConfig commons.
STDIO_KEYS = {"command", "args", "env", "env_vars", "cwd"}
HTTP_KEYS = {
    "url",
    "bearer_token_env_var",
    "http_headers",
    "env_http_headers",
    "http_headers_helper",
}
COMMON_KEYS = {
    "enabled",
    "required",
    "startup_timeout_sec",
    "tool_timeout_sec",
    "enabled_tools",
    "disabled_tools",
    "default_tools_approval_mode",
    "tools",
    "supports_parallel_tool_calls",
    "omit_tools_from",
    "environment_id",
    "auth",
    "scopes",
    "oauth",
    "oauth_resource",
}


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else ".codex/config.toml")
    try:
        data = tomllib.loads(path.read_text())
    except FileNotFoundError:
        print(f"  ✗ {path} not found — run: just sync-mcp")
        return 1
    except tomllib.TOMLDecodeError as exc:
        print(f"  ✗ {path} is not valid TOML: {exc}")
        return 1

    errors = []

    if "mcpServers" in data:
        errors.append(
            "found `mcpServers` — Codex only reads `mcp_servers` (snake_case)"
        )

    for name, server in (data.get("mcp_servers") or {}).items():
        where = f"mcp_servers.{name}"
        if not isinstance(server, dict):
            errors.append(f"{where} is not a table")
            continue
        has_cmd, has_url = "command" in server, "url" in server
        if has_cmd and has_url:
            errors.append(f"{where} sets both `command` and `url` — pick one transport")
        elif not has_cmd and not has_url:
            errors.append(f"{where} sets neither `command` nor `url`")
        allowed = COMMON_KEYS | (STDIO_KEYS if has_cmd else HTTP_KEYS)
        for key in sorted(set(server) - allowed):
            hint = " (transport is inferred from command/url)" if key == "type" else ""
            errors.append(f"{where}.{key} is not a key Codex accepts{hint}")
        if has_cmd and not isinstance(server["command"], str):
            errors.append(
                f"{where}.command must be a single string; argv goes in `args`"
            )

    for err in errors:
        print(f"  ✗ {err}")
    if errors:
        print("    fix mcp/servers.toml or codex/config-base.toml, then: just sync-mcp")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
