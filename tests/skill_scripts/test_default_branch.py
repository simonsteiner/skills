"""Tests for skills/engineering/sync-and-branch/scripts/default-branch.sh, against throwaway repos.

    python3 -m unittest discover -s tests -t .
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills/engineering/sync-and-branch/scripts/default-branch.sh"

# A git hook running the suite exports GIT_DIR, GIT_INDEX_FILE, …; they'd point every call at the outer repo.
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, env=ENV, capture_output=True, text=True, check=True).stdout.strip()


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
        return subprocess.run([str(SCRIPT), *args], cwd=self.clone, env=ENV, capture_output=True, text=True, check=False)

    def test_reads_the_remote_head(self):
        result = self.run_script()
        self.assertEqual((result.returncode, result.stdout), (0, "trunk\n"), result.stderr)

    def test_asks_the_remote_when_head_is_missing(self):
        git(self.clone, "remote", "set-head", "origin", "--delete")
        result = self.run_script("origin")
        self.assertEqual((result.returncode, result.stdout), (0, "trunk\n"), result.stderr)

    def test_asks_the_remote_when_head_names_a_gone_branch(self):
        git(self.upstream, "branch", "-m", "trunk", "main")
        git(self.clone, "fetch", "-q", "--prune", "origin")
        result = self.run_script()
        self.assertEqual((result.returncode, result.stdout), (0, "main\n"), result.stderr)

    def test_refresh_sees_a_switched_default_whose_old_branch_was_kept(self):
        git(self.upstream, "switch", "-q", "-c", "main")
        git(self.clone, "fetch", "-q", "--prune", "origin")
        self.assertEqual(self.run_script().stdout, "trunk\n")  # cached, as documented
        result = self.run_script("--refresh")
        self.assertEqual((result.returncode, result.stdout), (0, "main\n"), result.stderr)

    def test_a_local_branch_named_like_the_remote_ref_is_ignored(self):
        git(self.clone, "branch", "origin/trunk")
        result = self.run_script()
        self.assertEqual((result.returncode, result.stdout), (0, "trunk\n"), result.stderr)

    def test_a_remote_with_no_default_branch_exits_1(self):
        empty = self.clone.parent / "empty.git"
        git(self.clone.parent, "init", "-q", "--bare", str(empty))
        git(self.clone, "remote", "add", "e", str(empty))
        result = self.run_script("e")
        self.assertEqual(result.returncode, 1)
        self.assertIn("'e'", result.stderr)

    def test_outside_a_repo_says_so(self):
        result = subprocess.run([str(SCRIPT)], cwd=self.clone.parent, env=ENV, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a git repository", result.stderr)

    def test_unknown_remote_exits_1(self):
        result = self.run_script("upstream")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no remote 'upstream'", result.stderr)

    def test_two_remotes_is_bad_usage(self):
        self.assertEqual(self.run_script("a", "b").returncode, 2)
        self.assertEqual(self.run_script("--bogus").returncode, 2)


if __name__ == "__main__":
    unittest.main()
