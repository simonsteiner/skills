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


def review(body, state="COMMENTED"):
    return {"state": state, "body": body}


class UnresolvedThreadsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.gh = FakeGh(tmp.name)
        self.gh.on("pr", "view", "--json", "number", json={"number": 7})
        self.gh.on("repo", "view", json={"nameWithOwner": "o/r"})
        self.gh.on("api", "user", json={"login": "me"})

    def run_with(self, reviews, threads, pr=None):
        self.gh.on("pr", "view", str(pr or 7), "--json", "reviews", json={"reviews": reviews})
        self.gh.on("api", "graphql", json={"data": {"repository": {"pullRequest": {"reviewThreads": {
            "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": threads}}}}})
        result = self.gh.run(SCRIPT, *([pr] if pr else []))
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


if __name__ == "__main__":
    unittest.main()
