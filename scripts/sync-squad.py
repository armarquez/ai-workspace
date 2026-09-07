#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# ///
"""Merge squad/config.json's profiles into claude-squad's global config.

Usage:
    sync-squad.py link   [--config PATH] [--profiles-file PATH]
    sync-squad.py unlink [--config PATH] [--profiles-file PATH]

squad/config.json is already claude-squad's own native format (confirmed against the real
binary, not secondhand docs — `claude-squad debug` round-trips a `profiles` array of
{name, program} unchanged), so there is no render step, only a merge: `link` adds/replaces
each profile by `name`; `unlink` removes only the names the profiles file defines, leaving
everything else in ~/.claude-squad/config.json (default_program, auto_yes, branch_prefix,
any hand-added profiles) untouched.

--config lets link/unlink run against a throwaway file instead of the real
~/.claude-squad/config.json, for testing.

--profiles-file points at a different profiles source than this repo's own
squad/config.json — e.g. `onboard-repo.py squad`'s generated
`<target>/.ai-workspace/squad-profiles.json`, so the same merge-by-name logic covers both
ai-workspace's own profiles and a target repo's.
"""

import datetime
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_FILE = REPO_ROOT / "squad" / "config.json"


def our_profiles(template_file: Path = TEMPLATE_FILE) -> list[dict]:
    return json.loads(template_file.read_text())["profiles"]


def our_names(template_file: Path = TEMPLATE_FILE) -> set[str]:
    return {p["name"] for p in our_profiles(template_file)}


def default_config_path() -> Path:
    return Path.home() / ".claude-squad" / "config.json"


def backup(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".{stamp}.bak")
    shutil.copy2(path, backup_path)
    print(f"backed up {path} -> {backup_path}")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"wrote {path}")


def cmd_link(config_path: Path, profiles_file: Path = TEMPLATE_FILE) -> None:
    existing = json.loads(config_path.read_text()) if config_path.exists() else {}
    profiles = list(existing.get("profiles", []))
    kept = [p for p in profiles if p.get("name") not in our_names(profiles_file)]
    existing = dict(existing)
    existing["profiles"] = kept + our_profiles(profiles_file)
    backup(config_path)
    write_json(config_path, existing)


def cmd_unlink(config_path: Path, profiles_file: Path = TEMPLATE_FILE) -> None:
    if not config_path.exists():
        return
    data = json.loads(config_path.read_text())
    profiles = data.get("profiles", [])
    kept = [p for p in profiles if p.get("name") not in our_names(profiles_file)]
    if len(kept) == len(profiles):
        return
    data = dict(data)
    if kept:
        data["profiles"] = kept
    else:
        data.pop("profiles", None)
    backup(config_path)
    write_json(config_path, data)


def _parse_flags(args: list[str]) -> tuple[Path, Path]:
    config_path = default_config_path()
    profiles_file = TEMPLATE_FILE
    it = iter(args)
    for arg in it:
        value = next(it, None)
        if value is None:
            sys.exit(f"{arg} requires a value")
        if arg == "--config":
            config_path = Path(value)
        elif arg == "--profiles-file":
            profiles_file = Path(value).expanduser().resolve()
        else:
            sys.exit(f"unknown flag: {arg}")
    return config_path, profiles_file


def main() -> None:
    match sys.argv[1:]:
        case ["link", *rest]:
            cmd_link(*_parse_flags(rest))
        case ["unlink", *rest]:
            cmd_unlink(*_parse_flags(rest))
        case _:
            sys.exit(__doc__)


if __name__ == "__main__":
    main()
