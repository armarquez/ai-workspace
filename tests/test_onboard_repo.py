"""Behavior tests for repository onboarding."""

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ONBOARD_SCRIPT = REPO_ROOT / "scripts" / "onboard-repo.py"


class CbmIndexTests(unittest.TestCase):
    """Verify code-graph indexing through the onboarding CLI."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.target = self.root / "target"
        self.target.mkdir()
        (self.target / "justfile").write_text("default:\n    @just --list\n")
        self.log = self.root / "invocations.jsonl"
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        binary = bin_dir / "codebase-memory-mcp"
        binary.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import os
                import sys

                args = sys.argv[1:]
                with open(os.environ["FAKE_CBM_LOG"], "a", encoding="utf-8") as log:
                    log.write(json.dumps(args) + "\\n")
                if args == ["cli", "--json", "list_projects"]:
                    target = os.environ["FAKE_CBM_TARGET"]
                    indexed = os.environ["FAKE_CBM_INDEXED"] == "1"
                    text = f"project {target} main" if indexed else "projects: 0"
                    print(json.dumps({"content": [{"type": "text", "text": text}]}))
                elif args == ["cli", "list_projects"]:
                    print("projects: 1")
                elif args[:3] == ["cli", "--progress", "index_repository"]:
                    print('{"status":"indexed"}')
                else:
                    raise SystemExit(f"unexpected arguments: {args}")
                """
            )
        )
        binary.chmod(0o755)
        self.env = os.environ | {
            "FAKE_CBM_LOG": str(self.log),
            "FAKE_CBM_TARGET": str(self.target),
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        }

    def run_onboarding(
        self, *, indexed: bool, artifact: bool = False
    ) -> subprocess.CompletedProcess[str]:
        """Run the public onboarding command with a controlled CBM response."""
        if artifact:
            artifact_path = self.target / ".codebase-memory" / "graph.db.zst"
            artifact_path.parent.mkdir(exist_ok=True)
            artifact_path.write_bytes(b"graph")
        env = self.env | {"FAKE_CBM_INDEXED": "1" if indexed else "0"}
        return subprocess.run(
            [
                sys.executable,
                str(ONBOARD_SCRIPT),
                "cbm-index",
                str(self.target),
                "--apply",
            ],
            capture_output=True,
            check=False,
            env=env,
            text=True,
        )

    def invocations(self) -> list[list[str]]:
        """Return calls made to the fake CBM executable."""
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_apply_skips_an_already_indexed_target(self) -> None:
        result = self.run_onboarding(indexed=True, artifact=True)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("already indexed with a shared artifact", result.stdout)
        self.assertEqual(self.invocations(), [["cli", "--json", "list_projects"]])
        self.assertIn("cbm-ensure:", (self.target / "justfile").read_text())

    def test_apply_indexes_an_unindexed_target(self) -> None:
        result = self.run_onboarding(indexed=False)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("indexed — projects now known to the graph", result.stdout)
        self.assertEqual(
            self.invocations(),
            [
                ["cli", "--json", "list_projects"],
                [
                    "cli",
                    "--progress",
                    "index_repository",
                    "--repo-path",
                    str(self.target),
                    "--name",
                    "target",
                    "--persistence",
                    "true",
                ],
                ["cli", "list_projects"],
            ],
        )

    def test_apply_rebuilds_when_only_the_local_index_exists(self) -> None:
        result = self.run_onboarding(indexed=True)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--persistence true", result.stdout)
        self.assertEqual(len(self.invocations()), 3)

    def test_apply_keeps_one_managed_recipe(self) -> None:
        first = self.run_onboarding(indexed=True, artifact=True)
        second = self.run_onboarding(indexed=True, artifact=True)

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        justfile = (self.target / "justfile").read_text()
        self.assertEqual(justfile.count("# BEGIN ai-workspace codebase-memory"), 1)


if __name__ == "__main__":
    unittest.main()
