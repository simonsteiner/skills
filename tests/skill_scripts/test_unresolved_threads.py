"""Tests for skills/engineering/address-review-findings/scripts/unresolved-threads.sh, through a fake gh.

    python3 -m unittest discover -s tests -t .
"""

import json
import tempfile
import unittest
from pathlib import Path

from .fake_gh import FakeGh

SCRIPT = (Path(__file__).resolve().parents[2]
          / "skills/engineering/address-review-findings/scripts/unresolved-threads.sh")


def thread(id, *authors, resolved=False, total=None):
    comments = [{"databaseId": i, "author": {"login": a}, "body": "b", "url": "u", "originalLine": 1, "diffHunk": "@@"}
                for i, a in enumerate(authors)]
    return {"id": id, "isResolved": resolved, "isOutdated": False, "path": "a.ts", "line": 3, "startLine": None,
            "comments": {"totalCount": total or len(comments), "nodes": comments}}


def review(body, state="COMMENTED", author="alice", bot=False, id=None):
    return {"id": id or hash((body, state, author)) % 10**6, "state": state, "body": body,
            "user": {"login": author, "type": "Bot" if bot else "User"}}


def comment(review_id, reply_to=None):
    return {"pull_request_review_id": review_id, "in_reply_to_id": reply_to}


class UnresolvedThreadsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.gh = FakeGh(tmp.name)
        self.gh.on("pr", "view", "--json", "number", json={"number": 7})
        self.gh.on("repo", "view", json={"nameWithOwner": "o/r"})
        self.gh.on("api", "user", json={"login": "me"})

    def run_with(self, reviews, threads, pr=None, env=None, comments=()):
        n, repo = pr or 7, "/".join((env or {}).get("GH_REPO", "o/r").split("/")[-2:])
        self.gh.on("api", f"repos/{repo}/pulls/{n}/reviews?per_page=100", pages=[reviews])
        self.gh.on("api", f"repos/{repo}/pulls/{n}/comments?per_page=100", pages=[list(comments)])
        self.gh.on("api", "graphql", json={"data": {"repository": {"pullRequest": {"reviewThreads": {
            "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": threads}}}}})
        result = self.gh.run(SCRIPT, *([pr] if pr else []), env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result, [json.loads(line) for line in result.stdout.splitlines()]

    def test_prints_unresolved_threads_for_the_current_branch_pr(self):
        _, threads = self.run_with([review("")], [thread("A", "bot"), thread("B", "bot", resolved=True),
                                                  thread("C", "bot", total=150)])
        self.assertEqual([(t["id"], t["commentCount"]) for t in threads], [("A", 1), ("C", 150)])
        [graphql] = [c["args"] for c in self.gh.calls if c["args"][:2] == ["api", "graphql"]]
        self.assertIn("--paginate", graphql)
        self.assertEqual(graphql[graphql.index("-F") + 1], "number=7")
        self.assertIn("owner=o", graphql)
        self.assertIn("repo=r", graphql)

    def test_gh_repo_wins_over_gh_repo_view(self):
        for gh_repo in ("fork/r2", "github.com/fork/r2"):
            with self.subTest(gh_repo=gh_repo):
                self.run_with([review("")], [], env={"GH_REPO": gh_repo})
                self.assertNotIn(["repo", "view"], [c["args"][:2] for c in self.gh.calls])
                [graphql] = [c["args"] for c in self.gh.calls if c["args"][:2] == ["api", "graphql"]]
                self.assertIn("owner=fork", graphql)
                self.assertIn("repo=r2", graphql)

    def test_awaiting_reviewer_only_when_you_answered_someone_else_last(self):
        _, threads = self.run_with([review("")], [thread("A", "bot", "me"), thread("B", "bot", "me", "bot"),
                                                  thread("C", "me"), thread("D", "me", "me")], pr=9)
        self.assertEqual({t["id"]: t["awaitingReviewer"] for t in threads},
                         {"A": True, "B": False, "C": False, "D": False})

    def test_warns_when_no_review_is_real(self):
        failed = [review("Copilot encountered an error while reviewing."), review("Rate limit exceeded."),
                  review("", state="PENDING")]
        result, _ = self.run_with(failed, [])
        self.assertIn("warning: PR #7 has no real review", result.stderr)

    def test_a_long_review_mentioning_rate_limits_is_real(self):
        result, _ = self.run_with([review("The rate limit check is wrong. " + "x" * 300)], [])
        self.assertEqual(result.stderr, "")

    def test_warns_when_only_bots_reviewed_but_lists_their_threads(self):
        bots = [review("Actionable comments posted: 2. " + "x" * 300, author="coderabbitai[bot]", bot=True),
                review("Looks fine.", author="copilot-pull-request-reviewer[bot]", bot=True),
                review("1 issue.", author="some-scanner", bot=True)]
        result, threads = self.run_with(bots, [thread("A", "coderabbitai")])
        self.assertIn("has no real review — only bot reviews (coderabbitai[bot], "
                      "copilot-pull-request-reviewer[bot], some-scanner)", result.stderr)
        self.assertEqual([t["id"] for t in threads], ["A"])

    def test_a_human_review_beside_a_bot_review_is_real(self):
        result, _ = self.run_with([review("Two nits.", author="coderabbitai[bot]", bot=True),
                                   review("LGTM", author="alice")], [])
        self.assertEqual(result.stderr, "")

    def test_thread_replies_are_not_a_review(self):
        bot, reply = review("Two nits.", author="coderabbitai[bot]", bot=True, id=1), review("", author="me", id=2)
        result, _ = self.run_with([bot, reply], [], comments=[comment(1), comment(2, reply_to=10)])
        self.assertIn("only bot reviews (coderabbitai[bot])", result.stderr)

    def test_an_empty_review_with_its_own_inline_comment_is_real(self):
        result, _ = self.run_with([review("", author="alice", id=3)], [], comments=[comment(3)])
        self.assertEqual(result.stderr, "")

    def test_an_empty_approval_is_real(self):
        result, _ = self.run_with([review("", state="APPROVED", author="alice")], [])
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
