"""Tests for skills/engineering/address-review-findings/scripts/push-once.sh, in throwaway repos.

    python3 -m unittest discover -s tests -t .
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from .fake_gh import FakeGh

SCRIPT = Path(__file__).resolve().parents[2] / "skills/engineering/address-review-findings/scripts/push-once.sh"
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
ENV.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
           GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")


class PushOnceTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.gh = FakeGh(tmp.name)
        self.remote = self.tmp / "remote.git"
        self.git("init", "-q", "--bare", str(self.remote), cwd=self.tmp)
        self.repo = self.clone("repo")
        self.commit("base", cwd=self.repo)
        self.git("push", "-q", "origin", "HEAD:refs/heads/feature")
        self.start = self.head()

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.repo, env=ENV, capture_output=True,
                              text=True, check=True).stdout.strip()

    def clone(self, name):
        self.git("clone", "-q", str(self.remote), name, cwd=self.tmp)
        return self.tmp / name

    def commit(self, name, cwd=None):
        (Path(cwd or self.repo) / name).write_text(name)
        self.git("add", name, cwd=cwd)
        self.git("commit", "-q", "-m", name, cwd=cwd)

    def head(self, cwd=None):
        return self.git("rev-parse", "HEAD", cwd=cwd)

    def remote_head(self):
        return self.git("rev-parse", "refs/heads/feature", cwd=self.remote)

    def push_once(self, *args, cwd=None):
        return self.gh.run(SCRIPT, *args, env=ENV, cwd=cwd or self.repo)

    def test_pushes_the_round_and_prints_the_commit(self):
        self.commit("fix1")
        self.commit("fix2")
        result = self.push_once(self.start, 2, "feature")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), self.head())
        self.assertEqual(self.remote_head(), self.head())
        self.assertEqual(self.gh.calls, [])

    def test_wrong_count_pushes_nothing_and_lists_the_commits(self):
        self.commit("fix1")
        self.commit("fix2")
        result = self.push_once(self.start, 1, "feature")
        self.assertEqual(result.returncode, 1)
        self.assertIn("expected 1 commit(s)", result.stderr)
        self.assertIn("fix2", result.stderr)
        self.assertEqual(self.remote_head(), self.start)

    def test_uncommitted_change_pushes_nothing(self):
        self.commit("fix1")
        (self.repo / "fix1").write_text("edited, not committed")
        result = self.push_once(self.start, 1, "feature")
        self.assertEqual(result.returncode, 1)
        self.assertIn("uncommitted changes", result.stderr)
        self.assertEqual(self.remote_head(), self.start)

    def test_untracked_scratch_files_dont_block(self):
        self.commit("fix1")
        (self.repo / ".scratch").mkdir()
        (self.repo / ".scratch" / "notes").write_text("scratch")
        result = self.push_once(self.start, 1, "feature")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("untracked", result.stderr)

    def test_start_not_an_ancestor_pushes_nothing(self):
        self.git("checkout", "-q", "--orphan", "other")
        self.commit("unrelated")
        result = self.push_once(self.start, 1, "feature")
        self.assertEqual(result.returncode, 1)
        self.assertIn("isn't an ancestor", result.stderr)
        self.assertEqual(self.remote_head(), self.start)

    def test_zero_commits_is_refused(self):
        result = self.push_once(self.start, 0, "feature")
        self.assertEqual(result.returncode, 1)
        self.assertIn("nothing to push", result.stderr)

    def test_bare_repo_is_refused(self):
        result = self.push_once(self.start, 1, "feature", cwd=self.remote)
        self.assertEqual(result.returncode, 1)
        self.assertIn("not inside a work tree", result.stderr)

    def test_carry_up_merge_counts_as_one(self):
        # The lower layer gains two fix commits; merging them into the upper layer is one commit on its branch.
        lower = self.clone("lower")
        self.git("checkout", "-q", "-b", "lower", self.start, cwd=lower)
        self.commit("lower-fix1", cwd=lower)
        self.commit("lower-fix2", cwd=lower)
        self.git("push", "-q", "origin", "HEAD:refs/heads/lower", cwd=lower)
        self.commit("upper-own")
        self.git("push", "-q", "origin", "HEAD:refs/heads/feature")
        upper_start = self.head()
        self.git("fetch", "-q", "origin")
        self.git("merge", "-q", "--no-edit", "origin/lower")
        self.commit("upper-fix")
        result = self.push_once(upper_start, 2, "feature")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_head(), self.head())

    def test_rejected_push_exits_3_and_the_rerun_after_the_merge_pushes(self):
        other = self.clone("other")
        self.git("checkout", "-q", "-b", "feature", "origin/feature", cwd=other)
        self.commit("someone-else", cwd=other)
        self.git("push", "-q", "origin", "HEAD:refs/heads/feature", cwd=other)
        self.commit("fix1")
        result = self.push_once(self.start, 1, "feature")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("rerun with 2 commits", result.stderr)
        self.git("fetch", "-q", "origin")
        self.git("merge", "-q", "--no-edit", "origin/feature")
        result = self.push_once(self.start, 2, "feature")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_head(), self.head())

    def test_other_push_failure_exits_4_and_keeps_the_count(self):
        self.commit("fix1")
        result = self.push_once(self.start, 1, "feature", str(self.tmp / "missing.git"))
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertIn("same count (1)", result.stderr)
        self.assertNotIn("rerun with 2", result.stderr)

    def test_failing_pre_push_hook_exits_4(self):
        self.commit("fix1")
        hook = self.repo / ".git" / "hooks" / "pre-push"
        hook.write_text("#!/bin/sh\necho 'hook says no' >&2\nexit 1\n")
        hook.chmod(0o755)
        result = self.push_once(self.start, 1, "feature")
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertEqual(self.remote_head(), self.start)

    def test_detached_worktree_pushes_to_a_url_remote(self):
        # Step 0 gives the PR a detached worktree, and a fork's PR passes the fork's URL as the remote.
        wt = self.tmp / "wt"
        self.git("worktree", "add", "-q", "--detach", str(wt), self.start)
        self.commit("fix1", cwd=wt)
        result = self.push_once(self.start, 1, "feature", str(self.remote), cwd=wt)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_head(), self.head(cwd=wt))

    def test_unfinished_merge_pushes_nothing(self):
        # Every conflict staged as "ours" leaves an empty status but a MERGE_HEAD.
        lower = self.clone("lower")
        self.git("checkout", "-q", "-b", "lower", self.start, cwd=lower)
        (lower / "base").write_text("lower")
        self.git("commit", "-q", "-am", "lower", cwd=lower)
        self.git("push", "-q", "origin", "HEAD:refs/heads/lower", cwd=lower)
        (self.repo / "base").write_text("upper")
        self.git("commit", "-q", "-am", "upper")
        self.git("fetch", "-q", "origin")
        subprocess.run(["git", "merge", "--no-edit", "origin/lower"], check=False, cwd=self.repo, env=ENV, capture_output=True)  # conflicts on purpose
        self.git("checkout", "--ours", "base")
        self.git("add", "base")
        result = self.push_once(self.start, 1, "feature")
        self.assertEqual(result.returncode, 1)
        self.assertIn("MERGE_HEAD", result.stderr)
        self.assertEqual(self.remote_head(), self.start)

    def test_untracked_new_file_is_named_but_doesnt_block(self):
        self.commit("fix1")
        (self.repo / "newtest.py").write_text("never added")
        result = self.push_once(self.start, 1, "feature")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("newtest.py", result.stderr)


if __name__ == "__main__":
    unittest.main()
