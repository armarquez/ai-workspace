#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# ///
"""Render mcp/servers.toml into each CLI's native MCP config format.

Usage:
    sync-mcp.py render                    write repo-scoped config files
    sync-mcp.py link   <claude|antigravity|opencode>   merge into $HOME
    sync-mcp.py unlink <claude|antigravity|opencode>   restore from backup

No standard MCP config format exists yet (SEP-2633 is unmerged), so this
script owns the translation instead of depending on a third-party syncer that
writes ~/.claude.json directly.
"""

import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVERS_FILE = REPO_ROOT / "mcp" / "servers.toml"


def load_servers() -> dict:
    with SERVERS_FILE.open("rb") as f:
        return tomllib.load(f)


def stdio_entry(server: dict) -> dict:
    entry = {
        "type": "stdio",
        "command": server["command"],
        "args": server.get("args", []),
    }
    if "env" in server:
        entry["env"] = server["env"]
    return entry


def render_claude(servers: dict) -> dict:
    return {"mcpServers": {name: stdio_entry(s) for name, s in servers.items()}}


def render_antigravity(servers: dict) -> dict:
    # Antigravity uses the same stdio shape as Claude Code, but remote
    # servers use `serverUrl`, not `url`/`httpUrl` — no remote servers yet.
    # Its documented examples omit a "type" key for stdio entries; whether it
    # tolerates one is unverified (agy is not installed on this machine) —
    # check `agy mcp list` after the first real `just antigravity link`.
    return {"mcpServers": {name: stdio_entry(s) for name, s in servers.items()}}


def render_opencode(servers: dict) -> dict:
    mcp = {}
    for name, s in servers.items():
        mcp[name] = {
            "type": "local",
            "command": [s["command"], *s.get("args", [])],
            "enabled": True,
        }
        if "env" in s:
            mcp[name]["environment"] = s["env"]
    return mcp


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"wrote {path.relative_to(REPO_ROOT)}")


def cmd_render() -> None:
    servers = load_servers()

    write_json(REPO_ROOT / ".mcp.json", render_claude(servers))
    write_json(REPO_ROOT / ".agents" / "mcp_config.json", render_antigravity(servers))

    opencode_config = json.loads(
        (REPO_ROOT / "opencode" / "providers.json").read_text()
    )
    opencode_config["$schema"] = "https://opencode.ai/config.json"
    opencode_config["mcp"] = render_opencode(servers)
    write_json(REPO_ROOT / "opencode.json", opencode_config)


def backup(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".{stamp}.bak")
    shutil.copy2(path, backup_path)
    print(f"backed up {path} -> {backup_path}")


def merge_json_file(path: Path, key: str, new_values: dict) -> None:
    existing = {}
    if path.exists():
        backup(path)
        existing = json.loads(path.read_text())
    existing.setdefault(key, {})
    existing[key].update(new_values)
    write_json(path, existing)


def cmd_link(provider: str) -> None:
    servers = load_servers()
    if provider == "claude":
        for name, s in servers.items():
            payload = json.dumps(stdio_entry(s))
            subprocess.run(
                ["claude", "mcp", "add-json", name, payload, "-s", "user"],
                check=False,  # non-zero if already registered; not fatal
            )
    elif provider == "antigravity":
        path = Path.home() / ".gemini" / "config" / "mcp_config.json"
        merge_json_file(path, "mcpServers", render_antigravity(servers)["mcpServers"])
    elif provider == "opencode":
        path = Path.home() / ".config" / "opencode" / "opencode.json"
        merge_json_file(path, "mcp", render_opencode(servers))
    else:
        sys.exit(f"unknown provider: {provider}")


def cmd_unlink(provider: str) -> None:
    servers = load_servers()
    if provider == "claude":
        for name in servers:
            subprocess.run(["claude", "mcp", "remove", name, "-s", "user"], check=False)
    elif provider == "antigravity":
        path = Path.home() / ".gemini" / "config" / "mcp_config.json"
        _remove_keys(path, "mcpServers", servers.keys())
    elif provider == "opencode":
        path = Path.home() / ".config" / "opencode" / "opencode.json"
        _remove_keys(path, "mcp", servers.keys())
    else:
        sys.exit(f"unknown provider: {provider}")


def _remove_keys(path: Path, key: str, names) -> None:
    if not path.exists():
        return
    backup(path)
    data = json.loads(path.read_text())
    for name in names:
        data.get(key, {}).pop(name, None)
    write_json(path, data)


def main() -> None:
    match sys.argv[1:]:
        case ["render"]:
            cmd_render()
        case ["link", provider]:
            cmd_link(provider)
        case ["unlink", provider]:
            cmd_unlink(provider)
        case _:
            sys.exit(__doc__)


if __name__ == "__main__":
    main()
