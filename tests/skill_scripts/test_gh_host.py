"""Host resolution reaches `gh api` as GH_HOST in every script that calls it.

`gh api` takes its host from GH_HOST or --hostname, never from GH_REPO or the checkout, so
without this a GitHub Enterprise GH_REPO=<host>/<owner>/<repo> or Enterprise checkout would
send the calls to github.com.

    uv run --locked --no-build python3 -m unittest discover -s tests -t .
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
    ("review-prs/scripts/review-threads.sh", ["12"], ""),
]


class GhHostTest(unittest.TestCase):
    def first_call(self, script, args, stdin, gh_repo):
        with tempfile.TemporaryDirectory() as tmp:
            gh = FakeGh(tmp)
            gh.run(SKILLS / script, *args, stdin=stdin, env={"GH_REPO": gh_repo}, cwd=tmp)
            self.assertTrue(gh.calls, f"{script} made no gh call")
            return gh.calls[0]

    def test_host_qualified_gh_repo_sets_gh_host(self):
        for script, args, stdin in CASES:
            with self.subTest(script=script):
                call = self.first_call(script, args, stdin, "ghe.example.com/acme/web")
                self.assertNotEqual(call["args"][:2], ["repo", "view"])
                self.assertEqual(call["env"].get("GH_HOST"), "ghe.example.com")

    def test_owner_repo_leaves_gh_host_unset(self):
        for script, args, stdin in CASES:
            with self.subTest(script=script):
                call = self.first_call(script, args, stdin, "acme/web")
                self.assertNotEqual(call["args"][:2], ["repo", "view"])
                self.assertNotIn("GH_HOST", call["env"])

    def test_enterprise_checkout_without_gh_repo_sets_gh_host(self):
        for script, args, stdin in CASES:
            with self.subTest(script=script), tempfile.TemporaryDirectory() as tmp:
                gh = FakeGh(tmp)
                gh.on("repo", "view", json={"url": "https://ghe.example.com/acme/web"})
                gh.on("pr", "view", json={"headRefOid": "abc123"})
                gh.run(SKILLS / script, *args, stdin=stdin, cwd=tmp)
                api = [c for c in gh.calls if c["args"][:1] == ["api"]]
                self.assertTrue(api, f"{script} made no gh api call: {gh.calls}")
                self.assertEqual({c["env"].get("GH_HOST") for c in api}, {"ghe.example.com"})

    def test_explicit_gh_host_without_gh_repo_is_preserved(self):
        needs_owner_repo = {
            "address-review-findings/scripts/unresolved-threads.sh",
            "review-prs/scripts/review-threads.sh",
        }
        for script, args, stdin in CASES:
            with self.subTest(script=script), tempfile.TemporaryDirectory() as tmp:
                gh = FakeGh(tmp)
                gh.on("repo", "view", json={"url": "https://github.com/acme/web"})
                gh.on("pr", "view", json={"headRefOid": "abc123"})
                gh.run(SKILLS / script, *args, stdin=stdin, env={"GH_HOST": "ghe.example.com"}, cwd=tmp)
                api = [c for c in gh.calls if c["args"][:1] == ["api"]]
                self.assertTrue(api, f"{script} made no gh api call: {gh.calls}")
                self.assertEqual({c["env"].get("GH_HOST") for c in api}, {"ghe.example.com"})
                if script not in needs_owner_repo:
                    self.assertFalse(any(c["args"][:2] == ["repo", "view"] for c in gh.calls), gh.calls)


if __name__ == "__main__":
    unittest.main()
