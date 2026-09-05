#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# ///
"""Render a rules/master/-shaped input folder into each agent's own folder, then into
each agent's native global ($HOME) config.

Usage:
    sync-rules.py render [--input DIR] [--output DIR]
        write <output>/claude/ and <output>/codex/ from <input> (defaults: rules/master/, rules/)
    sync-rules.py check [--input DIR]
        read-only: does <input> (rendered for Claude) match live ~/.claude?
    sync-rules.py link   <codex> [--input DIR]
        merge <input>, rendered for Codex, into ~/.codex/
    sync-rules.py unlink <codex>
        remove only what this repo added

--input/--output let render/check/link run against a throwaway folder instead of this
repo's own rules/master/ and rules/ — useful for testing the render logic in isolation.

rules/master/ is a vendored, byte-for-byte copy of ~/dotfiles/claude/base's CLAUDE.md +
rules/*.md — the actual global rules Claude Code loads, stowed there by dotfiles. Airbnb-
specific rules (~/dotfiles/claude/airbnb/) are deliberately not vendored here; this repo
stays free of internal/company references.

rules/claude/ and rules/codex/ are generated (gitignored, like .mcp.json) — never hand-edit
them. For Claude, `render` is an identity copy: dotfiles' stow is still what actually
owns ~/.claude, so `link`/`unlink` refuse "claude" — `check` instead proves the render
still matches what's live there. For Codex, the same master/ corpus is concatenated into
one ~/.codex/AGENTS.md, since Codex reads a single global instructions file rather than a
directory of them — content Codex never had before this.

Codex's hooks.json stdin payload and blocking convention are identical to Claude's
(exit 2 + reason on stderr blocks the call; the command is read from
`.tool_input.command`) — see https://developers.openai.com/codex/hooks.
"""

import datetime
import json
import os
import shutil
import sys
from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = REPO_ROOT / "rules"
DEFAULT_MASTER_DIR = RULES_DIR / "master"

BEGIN_MARKER = "<!-- BEGIN ai-workspace rules -->"
END_MARKER = "<!-- END ai-workspace rules -->"
# Embedded as a leading shell comment in each rendered hook command, so link/unlink can
# find and remove only this repo's own entries without disturbing hand-written ones.
HOOK_MARKER_PREFIX = "# ai-workspace:"


def master_corpus(master: Path) -> list[tuple[str, Path]]:
    """(label, path) pairs: CLAUDE.md first, then each topics/*.md, sorted."""
    corpus = [("CLAUDE.md", master / "CLAUDE.md")]
    corpus += [(path.name, path) for path in sorted((master / "topics").glob("*.md"))]
    return corpus


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))


def claude_home() -> Path:
    """Not read by the real `claude` binary — this script's own override knob for
    testing `check` without touching a real ~/.claude."""
    return Path(
        os.environ.get("AI_WORKSPACE_CLAUDE_HOME", str(Path.home() / ".claude"))
    )


def backup(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".{stamp}.bak")
    shutil.copy2(path, backup_path)
    print(f"backed up {path} -> {backup_path}")


def _display(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n")
    print(f"wrote {_display(path)}")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"wrote {_display(path)}")


def agents_md_block(master: Path) -> str:
    # No trailing newline after END_MARKER: write_text() normalizes to exactly one, and
    # a re-link's partition(END_MARKER) would otherwise pick up a prior write's trailing
    # newline as `post`, compounding one extra blank line onto the file on every re-link.
    sections = "\n\n---\n\n".join(
        path.read_text().strip() for _, path in master_corpus(master)
    )
    return f"{BEGIN_MARKER}\n{sections}\n{END_MARKER}"


def codex_hook_groups(master: Path) -> dict[str, list[dict]]:
    """Event name -> list of matcher groups, ready to nest under hooks.json's "hooks" key."""
    with (master / "hooks.toml").open("rb") as f:
        hooks = tomllib.load(f)["hooks"]
    groups: dict[str, list[dict]] = {}
    for hook in hooks:
        command = f"{HOOK_MARKER_PREFIX}{hook['id']}\n{hook['command']}"
        group = {
            "matcher": hook["matcher"],
            "hooks": [{"type": "command", "command": command}],
        }
        groups.setdefault(hook["event"], []).append(group)
    return groups


def _is_ours(group: dict) -> bool:
    return any(
        HOOK_MARKER_PREFIX in h.get("command", "") for h in group.get("hooks", [])
    )


def _merge_agents_md(existing: str, block: str) -> str:
    if BEGIN_MARKER in existing and END_MARKER in existing:
        pre, _, rest = existing.partition(BEGIN_MARKER)
        _, _, post = rest.partition(END_MARKER)
        return pre + block + post
    sep = "\n" if existing and not existing.endswith("\n") else ""
    return existing + sep + block


def _merge_hooks_json(existing: dict, our_groups: dict[str, list[dict]]) -> dict:
    hooks = dict(existing.get("hooks", {}))
    for event, groups in our_groups.items():
        kept = [g for g in hooks.get(event, []) if not _is_ours(g)]
        hooks[event] = kept + groups
    existing = dict(existing)
    existing["hooks"] = hooks
    return existing


def _unlink_hooks_json(data: dict) -> tuple[dict, bool]:
    hooks = dict(data.get("hooks", {}))
    changed = False
    for event in list(hooks.keys()):
        kept = [g for g in hooks[event] if not _is_ours(g)]
        changed = changed or len(kept) != len(hooks[event])
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event)
    data = dict(data)
    data["hooks"] = hooks
    return data, changed


def cmd_render(input_dir: Path | None = None, output_dir: Path | None = None) -> None:
    master = input_dir or DEFAULT_MASTER_DIR
    out = output_dir or RULES_DIR

    write_text(out / "claude" / "CLAUDE.md", (master / "CLAUDE.md").read_text())
    for label, path in master_corpus(master)[1:]:
        write_text(out / "claude" / "rules" / label, path.read_text())

    write_text(out / "codex" / "AGENTS.md", agents_md_block(master))
    write_json(out / "codex" / "hooks.json", {"hooks": codex_hook_groups(master)})


def cmd_check(input_dir: Path | None = None) -> None:
    """Read-only: does <input> (rendered for Claude) match what dotfiles' stow puts at
    live ~/.claude? Never writes — Claude's global rules stay owned by dotfiles, this
    only proves the vendored copy hasn't drifted from it."""
    master = input_dir or DEFAULT_MASTER_DIR
    home = claude_home()
    drifted = False
    for label, vendored in master_corpus(master):
        live = home / "CLAUDE.md" if label == "CLAUDE.md" else home / "rules" / label
        if not live.exists():
            print(
                f"  ? {label}: not found at {live} (dotfiles not stowed on this machine?)"
            )
            drifted = True
        elif vendored.read_text() != live.read_text():
            print(f"  ✗ {label}: differs from {live}")
            drifted = True
        else:
            print(f"  ✓ {label}: matches {live}")

    if drifted:
        sys.exit(
            f"\n{_display(master)} has drifted from ~/dotfiles/claude — re-copy from "
            "there (or, if this ran on a machine without dotfiles stowed, that mismatch "
            "is expected)."
        )
    print(f"\n{_display(master)} matches ~/.claude exactly.")


def cmd_link(provider: str, input_dir: Path | None = None) -> None:
    if provider == "claude":
        sys.exit(
            "claude's global rules stay owned by ~/dotfiles/claude (stow) — nothing for "
            "this script to link. Run `just check-rules` to verify the render still "
            "matches instead."
        )
    if provider != "codex":
        sys.exit(f"unknown provider: {provider}")
    master = input_dir or DEFAULT_MASTER_DIR

    agents_path = codex_home() / "AGENTS.md"
    existing_text = agents_path.read_text() if agents_path.exists() else ""
    backup(agents_path)
    write_text(agents_path, _merge_agents_md(existing_text, agents_md_block(master)))

    hooks_path = codex_home() / "hooks.json"
    existing_json = json.loads(hooks_path.read_text()) if hooks_path.exists() else {}
    backup(hooks_path)
    write_json(hooks_path, _merge_hooks_json(existing_json, codex_hook_groups(master)))


def cmd_unlink(provider: str) -> None:
    if provider == "claude":
        sys.exit(
            "claude's global rules stay owned by ~/dotfiles/claude (stow) — nothing to unlink."
        )
    if provider != "codex":
        sys.exit(f"unknown provider: {provider}")

    agents_path = codex_home() / "AGENTS.md"
    if agents_path.exists():
        text = agents_path.read_text()
        if BEGIN_MARKER in text:
            pre, _, rest = text.partition(BEGIN_MARKER)
            _, _, post = rest.partition(END_MARKER)
            backup(agents_path)
            write_text(agents_path, pre + post)

    hooks_path = codex_home() / "hooks.json"
    if hooks_path.exists():
        data, changed = _unlink_hooks_json(json.loads(hooks_path.read_text()))
        if changed:
            backup(hooks_path)
            write_json(hooks_path, data)


def _parse_flags(args: list[str], allowed: set[str]) -> dict[str, Path]:
    names = {"--input": "input_dir", "--output": "output_dir"}
    flags: dict[str, Path] = {}
    it = iter(args)
    for arg in it:
        key = names.get(arg)
        if key is None or key not in allowed:
            sys.exit(f"unknown or unsupported flag for this command: {arg}")
        value = next(it, None)
        if value is None:
            sys.exit(f"{arg} requires a value")
        flags[key] = Path(value)
    return flags


def main() -> None:
    match sys.argv[1:]:
        case ["render", *rest]:
            cmd_render(**_parse_flags(rest, {"input_dir", "output_dir"}))
        case ["check", *rest]:
            cmd_check(**_parse_flags(rest, {"input_dir"}))
        case ["link", provider, *rest]:
            cmd_link(provider, **_parse_flags(rest, {"input_dir"}))
        case ["unlink", provider]:
            cmd_unlink(provider)
        case _:
            sys.exit(__doc__)


if __name__ == "__main__":
    main()
