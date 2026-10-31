"""A host-qualified GH_REPO reaches `gh api` as GH_HOST in every script that calls it.

`gh api` takes its host from GH_HOST or --hostname, never from GH_REPO, so without this a
GitHub Enterprise GH_REPO=<host>/<owner>/<repo> would send the calls to github.com.

    python3 -m unittest discover -s tests -t .
"""

import tempfile
import unittest
from pathlib import Path

from .fake_gh import FakeGh

SKILLS = Path(__file__).resolve().parents[2] / "skills/engineering"
# Each script with arguments that pass its own checks, so its first gh call is made.
# With no rules the fake gh fails that call, which still logs the environment it got.
CASES = [
    ("address-review-findings/scripts/reply-resolve.sh", ["PRRT_abc"], "Fixed in abc1234."),
    ("address-review-findings/scripts/unresolved-threads.sh", ["12"], ""),
    ("review-prs/scripts/post-review.sh", ["12"], '{"body": "0 findings.", "comments": []}'),
    ("review-prs/scripts/note-fixes.sh", ["12", "34", "abc1234"], ""),
    ("review-prs/scripts/outside-findings.sh", ["12"], ""),
]


class GhHostTest(unittest.TestCase):
    def first_call_env(self, script, args, stdin, gh_repo):
        with tempfile.TemporaryDirectory() as tmp:
            gh = FakeGh(tmp)
            gh.run(SKILLS / script, *args, stdin=stdin, env={"GH_REPO": gh_repo}, cwd=tmp)
            self.assertTrue(gh.calls, f"{script} made no gh call")
            return gh.calls[0]["env"]

    def test_host_qualified_gh_repo_sets_gh_host(self):
        for script, args, stdin in CASES:
            with self.subTest(script=script):
                env = self.first_call_env(script, args, stdin, "ghe.example.com/acme/web")
                self.assertEqual(env.get("GH_HOST"), "ghe.example.com")

    def test_owner_repo_leaves_gh_host_unset(self):
        for script, args, stdin in CASES:
            with self.subTest(script=script):
                self.assertNotIn("GH_HOST", self.first_call_env(script, args, stdin, "acme/web"))


if __name__ == "__main__":
    unittest.main()
