"""Tests for scripts/sync-skills.py's checkout step, against throwaway git repos.

    uv run --locked --no-build python3 -m unittest discover -s tests -t .
"""

import contextlib
import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/sync-skills.py"
spec = importlib.util.spec_from_file_location("sync_skills", SCRIPT)
sync_skills = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_skills)


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


class CheckoutTest(unittest.TestCase):
    def setUp(self):
        # A git hook exports GIT_DIR, GIT_INDEX_FILE and friends; left in place they'd point
        # every git call here at the repo being committed instead of the throwaway ones.
        clean = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        patcher = mock.patch.dict(os.environ, clean, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        git(root, "init", "--quiet", "--bare", "--initial-branch=main", "origin.git")
        self.upstream = root / "upstream"
        git(root, "clone", "--quiet", "origin.git", "upstream")
        self.commit(self.upstream, "first")
        git(self.upstream, "push", "--quiet", "origin", "main")
        self.clone = root / "clone"
        git(root, "clone", "--quiet", "origin.git", "clone")
        git(self.clone, "remote", "set-head", "origin", "main")
        self.commit(self.upstream, "second")
        git(self.upstream, "push", "--quiet", "origin", "main")
        sync_skills.REPO = self.clone

    def commit(self, repo, message):
        git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com",
            "commit", "--quiet", "--allow-empty", "-m", message)

    def checkout(self, check):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = sync_skills.checkout(check)
        return status, out.getvalue().strip()

    def test_check_reports_commits_behind_and_moves_nothing(self):
        head = git(self.clone, "rev-parse", "HEAD")
        self.assertEqual(self.checkout(check=True), (1, "1 commit(s) behind origin/main; a sync pulls them"))
        self.assertEqual(git(self.clone, "rev-parse", "HEAD"), head)

    def test_sync_fast_forwards_the_default_branch(self):
        self.assertEqual(self.checkout(check=False), (0, "pulled 1 commit(s) from origin/main"))
        self.assertEqual(git(self.clone, "log", "-1", "--format=%s"), "second")
        self.assertEqual(self.checkout(check=False), (0, "up to date with origin/main"))

    def test_sync_leaves_another_branch_where_it_is(self):
        git(self.clone, "switch", "--quiet", "-c", "feat/x", "--track", "origin/main")
        self.assertEqual(self.checkout(check=False),
                         (0, "feat/x is 1 commit(s) behind origin/main; only main is pulled"))
        self.assertEqual(git(self.clone, "log", "-1", "--format=%s"), "first")

    def test_a_branch_with_no_upstream_is_not_pulled(self):
        git(self.clone, "switch", "--quiet", "-c", "local")
        self.assertEqual(self.checkout(check=False), (0, "this branch tracks no remote branch; not pulled"))


    def test_a_sync_that_pulls_reruns_the_updated_script(self):
        calls = []
        with mock.patch.object(sync_skills.os, "execve", side_effect=lambda *a: calls.append(a) or 0), \
             mock.patch.object(sync_skills, "finish", side_effect=lambda status, argv: status), \
             contextlib.redirect_stdout(io.StringIO()):
            sync_skills.main([])
        (_exe, args, env), = calls
        self.assertEqual(args[1:], [str(sync_skills.SCRIPTS / "sync-skills.py")])
        self.assertEqual(env[sync_skills.PULLED], "0")

    def test_the_rerun_skips_the_checkout(self):
        finish = mock.Mock(return_value=0)
        with mock.patch.dict(os.environ, {sync_skills.PULLED: "0"}), \
             mock.patch.object(sync_skills, "finish", finish), mock.patch.object(sync_skills, "checkout") as checkout:
            sync_skills.main([])
        checkout.assert_not_called()
        finish.assert_called_once_with(0, [])

if __name__ == "__main__":
    unittest.main()
