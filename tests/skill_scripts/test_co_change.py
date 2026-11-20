"""Tests for skills/engineering/arch-review/scripts/co-change.py, against throwaway repos.

    python3 -m unittest discover -s tests -t .
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/engineering/arch-review/scripts/co-change.py"

# A git hook running the suite exports GIT_DIR, GIT_INDEX_FILE, …; they'd point every call at the outer repo.
ENV = {**{k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}


class CoChangeTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.git("init", "-q")
        self.n = 0

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, env=ENV, capture_output=True, check=True)

    def commit(self, *paths):
        self.n += 1
        for path in paths:
            f = self.repo / path
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"{self.n}\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", f"c{self.n}")

    def run_script(self, *args, cwd=None):
        return subprocess.run([str(SCRIPT), *args], cwd=cwd or self.repo, env=ENV,
                              capture_output=True, text=True, check=False)

    def rows(self, *args):
        result = self.run_script(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return [line.split("\t") for line in result.stdout.splitlines()]

    def test_pairs_ranked_by_commits_together_with_share_of_the_rarer_file(self):
        for _ in range(3):
            self.commit("ui/menu.ts", "keys/keymap.ts")
        self.commit("ui/menu.ts")
        for _ in range(4):
            self.commit("a.py", "b.py")
        self.assertEqual(self.rows(), [["4", "100%", "a.py", "b.py"],
                                       ["3", "100%", "keys/keymap.ts", "ui/menu.ts"]])

    def test_pairs_below_min_are_dropped(self):
        self.commit("a.py", "b.py")
        self.commit("a.py", "b.py")
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.rows("--min", "2"), [["2", "100%", "a.py", "b.py"]])

    def test_share_counts_commits_of_either_file_alone(self):
        for _ in range(3):
            self.commit("a.py", "b.py")
        for _ in range(3):
            self.commit("a.py")
            self.commit("b.py")
        self.assertEqual(self.rows(), [["3", "50%", "a.py", "b.py"]])

    def test_sweeping_commits_are_skipped(self):
        for _ in range(3):
            self.commit("a.py", "b.py", "c.py")
        self.assertEqual(self.rows("--max-files", "2"), [])

    def test_deleted_files_are_dropped(self):
        for _ in range(3):
            self.commit("a.py", "old.py")
        self.git("rm", "-q", "old.py")
        self.git("commit", "-q", "-m", "drop")
        self.assertEqual(self.rows(), [])

    def test_paths_limit_the_files_counted(self):
        for _ in range(3):
            self.commit("src/a.py", "src/b.py", "docs/x.md")
        self.assertEqual(self.rows("src"), [["3", "100%", "src/a.py", "src/b.py"]])

    def test_sweep_cap_counts_files_outside_the_paths(self):
        for _ in range(3):
            self.commit("src/a.py", "src/b.py", "docs/x.md", "docs/y.md")
        self.assertEqual(self.rows("--max-files", "3", "src"), [])

    def test_paths_are_relative_to_the_current_directory(self):
        for _ in range(3):
            self.commit("src/a.py", "src/b.py", "docs/x.md")
        result = self.run_script(".", cwd=self.repo / "src")
        self.assertEqual(result.stdout.splitlines(), ["3\t100%\tsrc/a.py\tsrc/b.py"])

    def test_non_ascii_and_spaced_names_are_kept(self):
        for _ in range(3):
            self.commit("ä.py", "my file.py")
        self.assertEqual(self.rows(), [["3", "100%", "my file.py", "ä.py"]])

    def test_a_repo_without_commits_prints_nothing(self):
        self.assertEqual(self.rows(), [])

    def test_a_since_that_is_not_a_date_exits_2(self):
        self.commit("a.py")
        result = self.run_script("--since", "--output=/tmp/x")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--since", result.stderr)

    def test_top_limits_the_output(self):
        for _ in range(3):
            self.commit("a.py", "b.py", "c.py")
        self.assertEqual(len(self.rows("--top", "1")), 1)

    def test_outside_a_repo_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_script(cwd=tmp)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not inside a git repository", result.stderr)


if __name__ == "__main__":
    unittest.main()
