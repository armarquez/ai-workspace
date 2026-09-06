#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# ///
"""Bring an existing repo onto this toolkit: CLAUDE.md -> AGENTS.md, agent-CLI tool pins
in its mise.toml, and mcp/servers.toml's servers in its .mcp.json.

Usage:
    onboard-repo.py agents-md   <target> [--apply]
    onboard-repo.py mise-tools  <target> [--apply]
    onboard-repo.py mcp         <target> [--apply]
    onboard-repo.py all         <target> [--apply]
    onboard-repo.py check       <target>

Every mutating command is a dry-run (prints its plan, writes nothing) unless --apply is
passed. This script never runs git in the target repo — it only edits files on disk; the
user reviews and commits them in that repo's own workflow. Every write is backed up first,
same as every other script here.

Unlike sync-mcp.py/sync-rules.py/sync-squad.py, which only ever touch this repo or $HOME,
<target> is an arbitrary third-party repo path — the blast radius is higher, hence the
--apply gate on top of the usual backup-first convention.
"""

import datetime
import json
import re
import shutil
import sys
from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
MISE_FILE = REPO_ROOT / "mise.toml"
SERVERS_FILE = REPO_ROOT / "mcp" / "servers.toml"

# Agent-CLI tools this toolkit contributes to an onboarded repo's mise.toml. Deliberately
# excludes `ollama` (a separate opt-in fallback tier) and this repo's own scripting deps
# (uv/node/python/prek/gitleaks) — a target repo doesn't need those just to run the agents.
AGENT_TOOLS = ["claude", "agy", "opencode", "codex", "claude-squad", "tmux", "gh"]


def backup(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".{stamp}.bak")
    shutil.copy2(path, backup_path)
    print(f"backed up {path} -> {backup_path}")


def resolve_target(raw: str) -> Path:
    target = Path(raw).expanduser().resolve()
    if not target.is_dir():
        sys.exit(f"not a directory: {target}")
    return target


def _parse_flags(args: list[str]) -> tuple[str, bool]:
    """<target> [--apply] -> (target, apply)."""
    if not args:
        sys.exit("missing <target>")
    target, *rest = args
    apply = False
    for arg in rest:
        if arg == "--apply":
            apply = True
        else:
            sys.exit(f"unknown flag: {arg}")
    return target, apply


# --- agents-md ---------------------------------------------------------------


def cmd_agents_md(target: Path, apply: bool) -> None:
    claude_md = target / "CLAUDE.md"
    agents_md = target / "AGENTS.md"

    if not claude_md.exists():
        sys.exit(f"no CLAUDE.md at {target} — nothing to convert")

    content = claude_md.read_text()
    if content.lstrip().startswith("@AGENTS.md"):
        print(f"{claude_md} already starts with @AGENTS.md — nothing to do")
        return

    if agents_md.exists():
        sys.exit(
            f"{agents_md} already exists — merge by hand instead of overwriting it"
        )

    print(
        f"would write {agents_md} ({len(content.splitlines())} lines, from CLAUDE.md)"
    )
    print(f"would overwrite {claude_md} with '@AGENTS.md'")
    if not apply:
        print("(dry-run — pass --apply to write)")
        return

    backup(claude_md)
    agents_md.write_text(content)
    claude_md.write_text("@AGENTS.md\n")
    print(f"wrote {agents_md}")
    print(f"wrote {claude_md}")


# --- mise-tools ----------------------------------------------------------------


def _tool_basename(key: str) -> str:
    """A mise.toml tool key may be a backend-qualified spec like
    `github:armarquez/claude-squad` rather than a bare registry name like
    `claude-squad` — match AGENT_TOOLS against the name after the last `/`,
    so a fork pinned via a non-default backend is still recognized."""
    return key.rsplit("/", 1)[-1]


def _own_tool_lines() -> dict[str, str]:
    """Map tool name -> its exact source line (version + trailing comment) in this
    repo's own mise.toml, so a target repo's file carries the same provenance comment
    rather than a second, unlinked copy of the version."""
    lines = {}
    for line in MISE_FILE.read_text().splitlines():
        match = re.match(r'^([A-Za-z0-9_.-]+|"[^"]+")\s*=\s*"([^"]+)"', line)
        if not match:
            continue
        name = _tool_basename(match.group(1).strip('"'))
        if name in AGENT_TOOLS:
            lines[name] = line
    return lines


def _target_tools_table(target_mise: Path) -> dict[str, str]:
    if not target_mise.exists():
        return {}
    raw = tomllib.loads(target_mise.read_text()).get("tools", {})
    return {_tool_basename(key): value for key, value in raw.items()}


def _own_version(line: str) -> str:
    """Extract the pinned version from one of this repo's own mise.toml lines.
    Matches the quoted value after `=`, not just the first quoted substring —
    a backend-qualified key like `"github:armarquez/claude-squad"` is itself
    quoted, so a naive "first quoted string in the line" match would grab the
    key instead of the version."""
    match = re.search(r'=\s*"([^"]+)"', line)
    assert match, f"malformed mise.toml line: {line!r}"
    return match.group(1)


def _plan_mise_tools(target: Path) -> tuple[list[str], list[str]]:
    """Returns (lines_to_insert, report_lines)."""
    own_lines = _own_tool_lines()
    target_mise = target / "mise.toml"
    target_tools = _target_tools_table(target_mise)

    to_insert = []
    report = []
    for name in AGENT_TOOLS:
        if name not in own_lines:
            report.append(
                f"~ {name}: not pinned in ai-workspace's own mise.toml, skipping"
            )
            continue
        if name not in target_tools:
            to_insert.append(own_lines[name])
            report.append(
                f"+ {name}: missing from target — would add {own_lines[name].strip()}"
            )
        elif str(target_tools[name]) == _own_version(own_lines[name]):
            report.append(f"= {name}: already present, same version")
        else:
            report.append(
                f"! {name}: already present at {target_tools[name]!r}, "
                f"ai-workspace pins {_own_version(own_lines[name])!r} — "
                "conflict, not touching it, reconcile by hand"
            )
    return to_insert, report


def cmd_mise_tools(target: Path, apply: bool) -> None:
    target_mise = target / "mise.toml"
    if not target_mise.exists():
        sys.exit(f"no mise.toml at {target} — nothing to merge into")

    to_insert, report = _plan_mise_tools(target)
    print("\n".join(report))

    if not to_insert:
        print("nothing to add")
        return
    if not apply:
        print("(dry-run — pass --apply to write)")
        return

    lines = target_mise.read_text().splitlines()
    header_index = next(
        (i for i, line in enumerate(lines) if line.strip() == "[tools]"), None
    )
    if header_index is None:
        sys.exit(f"no [tools] table found in {target_mise} — add one by hand first")

    block = ["", "# --- added by ai-workspace onboarding ---", *to_insert]
    new_lines = lines[: header_index + 1] + block + lines[header_index + 1 :]

    backup(target_mise)
    target_mise.write_text("\n".join(new_lines) + "\n")
    print(f"wrote {target_mise}")


# --- mcp -------------------------------------------------------------------


def _load_servers() -> dict:
    with SERVERS_FILE.open("rb") as f:
        return tomllib.load(f)


def _stdio_entry(server: dict) -> dict:
    entry = {
        "type": "stdio",
        "command": server["command"],
        "args": server.get("args", []),
    }
    if "env" in server:
        entry["env"] = server["env"]
    return entry


def cmd_mcp(target: Path, apply: bool) -> None:
    servers = _load_servers()
    mcp_json = target / ".mcp.json"
    existing = json.loads(mcp_json.read_text()) if mcp_json.exists() else {}
    existing_servers = existing.get("mcpServers", {})

    for name in servers:
        if name in existing_servers:
            print(f"= {name}: already present in {mcp_json}, would update")
        else:
            print(f"+ {name}: would add to {mcp_json}")

    merged = dict(existing)
    merged.setdefault("mcpServers", {})
    merged["mcpServers"] = {
        **existing_servers,
        **{n: _stdio_entry(s) for n, s in servers.items()},
    }

    if merged == existing:
        print("nothing to update")
        return
    if not apply:
        print("(dry-run — pass --apply to write)")
        return

    backup(mcp_json)
    mcp_json.parent.mkdir(parents=True, exist_ok=True)
    mcp_json.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"wrote {mcp_json}")


# --- check -------------------------------------------------------------------


def cmd_check(target: Path) -> None:
    claude_md = target / "CLAUDE.md"
    agents_md = target / "AGENTS.md"
    if (
        agents_md.exists()
        and claude_md.exists()
        and claude_md.read_text().lstrip().startswith("@AGENTS.md")
    ):
        print(f"✓ {agents_md} exists, {claude_md} references it")
    elif agents_md.exists():
        print(f"~ {agents_md} exists but {claude_md} does not start with @AGENTS.md")
    else:
        print(f"✗ no {agents_md} — run: just onboard agents-md {target} --apply")

    _, report = _plan_mise_tools(target)
    print("\n".join(report))

    mcp_json = target / ".mcp.json"
    servers = _load_servers()
    existing = (
        json.loads(mcp_json.read_text()).get("mcpServers", {})
        if mcp_json.exists()
        else {}
    )
    for name in servers:
        if name in existing:
            print(f"✓ {name} present in {mcp_json}")
        else:
            print(
                f"✗ {name} missing from {mcp_json} — run: just onboard mcp {target} --apply"
            )


# --- main -------------------------------------------------------------------


def main() -> None:
    match sys.argv[1:]:
        case ["agents-md", *rest]:
            target, apply = _parse_flags(rest)
            cmd_agents_md(resolve_target(target), apply)
        case ["mise-tools", *rest]:
            target, apply = _parse_flags(rest)
            cmd_mise_tools(resolve_target(target), apply)
        case ["mcp", *rest]:
            target, apply = _parse_flags(rest)
            cmd_mcp(resolve_target(target), apply)
        case ["all", *rest]:
            target, apply = _parse_flags(rest)
            resolved = resolve_target(target)
            cmd_agents_md(resolved, apply)
            print()
            cmd_mise_tools(resolved, apply)
            print()
            cmd_mcp(resolved, apply)
        case ["check", target]:
            cmd_check(resolve_target(target))
        case _:
            sys.exit(__doc__)


if __name__ == "__main__":
    main()
