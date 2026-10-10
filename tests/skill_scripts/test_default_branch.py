"""Tests for skills/engineering/sync-and-branch/scripts/default-branch.sh, against throwaway repos.

    python3 -m unittest discover -s tests -t .
"""

import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills/engineering/sync-and-branch/scripts/default-branch.sh"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


class DefaultBranchTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.upstream, self.clone = root / "upstream", root / "clone"
        self.upstream.mkdir()
        git(self.upstream, "init", "-q", "-b", "trunk")
        git(self.upstream, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "init")
        git(root, "clone", "-q", str(self.upstream), str(self.clone))

    def run_script(self, *args):
        return subprocess.run([str(SCRIPT), *args], cwd=self.clone, capture_output=True, text=True, check=False)

    def test_reads_the_remote_head(self):
        result = self.run_script()
        self.assertEqual((result.returncode, result.stdout), (0, "trunk\n"), result.stderr)

    def test_asks_the_remote_when_head_is_missing(self):
        git(self.clone, "remote", "set-head", "origin", "--delete")
        self.assertEqual(self.run_script("origin").stdout, "trunk\n")

    def test_asks_the_remote_when_head_names_a_gone_branch(self):
        git(self.upstream, "branch", "-m", "trunk", "main")
        git(self.clone, "fetch", "-q", "--prune", "origin")
        self.assertEqual(self.run_script().stdout, "main\n")

    def test_unknown_remote_exits_1(self):
        result = self.run_script("upstream")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no remote 'upstream'", result.stderr)

    def test_two_remotes_is_bad_usage(self):
        self.assertEqual(self.run_script("a", "b").returncode, 2)


if __name__ == "__main__":
    unittest.main()
