"""Tests for scripts/sync-skills.py's checkout step, against throwaway git repos.

    uv run --locked --no-build python3 -m unittest discover -s tests -t .
"""

import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
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
        patcher = mock.patch.object(sync_skills, "REPO", self.clone)
        patcher.start()
        self.addCleanup(patcher.stop)

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

    def test_check_on_another_branch_reports_what_a_sync_does(self):
        git(self.clone, "switch", "--quiet", "-c", "feat/x", "--track", "origin/main")
        self.assertEqual(self.checkout(check=True),
                         (0, "feat/x is 1 commit(s) behind origin/main; only main is pulled"))

    def test_a_branch_with_no_upstream_is_not_pulled(self):
        git(self.clone, "switch", "--quiet", "-c", "local")
        self.assertEqual(self.checkout(check=False), (0, "this branch tracks no remote branch; not pulled"))


    def test_a_sync_pulls_then_reruns_the_pulled_copy_and_checks_out_once(self):
        # The command from a fixture checkout: a copy of sync-skills.py and stub siblings, which
        # are substituted at the process seam (each just says it ran).
        stub = "import sys; print('stub', __file__.rsplit('/', 1)[-1], *sys.argv[1:])\n"
        scripts = self.upstream / "scripts"
        scripts.mkdir()
        shutil.copy(SCRIPT, scripts / "sync-skills.py")
        for name in ("link-skills.py", "sync-third-party.py"):
            (scripts / name).write_text(stub)
        git(self.upstream, "add", "scripts")
        self.commit(self.upstream, "scripts")
        git(self.upstream, "push", "--quiet", "origin", "main")
        git(self.clone, "pull", "--quiet", "--ff-only")
        # Upstream then changes sync-skills.py: only the pulled copy prints "(pulled copy)".
        text = (scripts / "sync-skills.py").read_text()
        (scripts / "sync-skills.py").write_text(text.replace('"owned skills"', '"owned skills (pulled copy)"'))
        git(self.upstream, "add", "scripts")
        self.commit(self.upstream, "new sync-skills.py")
        git(self.upstream, "push", "--quiet", "origin", "main")

        done = subprocess.run([sys.executable, str(self.clone / "scripts/sync-skills.py")], cwd=self.clone,
                              capture_output=True, text=True, check=False)

        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(done.stdout.count("==> checkout"), 1)
        self.assertIn("pulled 1 commit(s) from origin/main", done.stdout)
        order = [done.stdout.index(x) for x in
                 ("==> checkout", "==> owned skills (pulled copy)", "stub link-skills.py",
                  "==> third-party skills", "stub sync-third-party.py")]
        self.assertEqual(order, sorted(order))


if __name__ == "__main__":
    unittest.main()
