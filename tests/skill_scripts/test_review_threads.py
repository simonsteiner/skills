"""Tests for skills/engineering/review-prs/scripts/review-threads.sh, through a fake gh.

    python3 -m unittest discover -s tests -t .
"""

import json
import tempfile
import unittest
from pathlib import Path

from .fake_gh import FakeGh

SCRIPT = Path(__file__).resolve().parents[2] / "skills/engineering/review-prs/scripts/review-threads.sh"


def thread(id, author, kind="User", resolved=False, outdated=False, line=3):
    return {"id": id, "isResolved": resolved, "isOutdated": outdated, "path": "a.ts", "line": line,
            "comments": {"nodes": [{"author": {"__typename": kind, "login": author}, "body": f"{id} body", "url": f"u/{id}"}]}}


def page(threads, more=False):
    return {"data": {"repository": {"pullRequest": {"reviewThreads": {
        "pageInfo": {"hasNextPage": more, "endCursor": "c" if more else None}, "nodes": threads}}}}}


class ReviewThreadsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.gh = FakeGh(tmp.name)
        self.gh.on("repo", "view", json={"url": "https://github.com/o/r"})

    def threads(self, *pages, env=None):
        self.gh.on("api", "graphql", pages=list(pages))
        result = self.gh.run(SCRIPT, 7, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return [json.loads(line) for line in result.stdout.splitlines()]

    def test_lists_resolved_and_unresolved_threads_across_pages(self):
        out = self.threads(page([thread("A", "coderabbitai", "Bot"), thread("B", "alice", resolved=True)], more=True),
                           page([thread("C", "copilot-pull-request-reviewer", "Bot", resolved=True, outdated=True, line=None)]))
        self.assertEqual(out, [
            {"id": "A", "resolved": False, "outdated": False, "path": "a.ts", "line": 3,
             "author": "coderabbitai", "bot": True, "body": "A body", "url": "u/A"},
            {"id": "B", "resolved": True, "outdated": False, "path": "a.ts", "line": 3,
             "author": "alice", "bot": False, "body": "B body", "url": "u/B"},
            {"id": "C", "resolved": True, "outdated": True, "path": "a.ts", "line": None,
             "author": "copilot-pull-request-reviewer", "bot": True, "body": "C body", "url": "u/C"},
        ])
        [graphql] = [c["args"] for c in self.gh.calls if c["args"][:2] == ["api", "graphql"]]
        self.assertIn("--paginate", graphql)
        # the fake returns every page whatever the query asks; real gh pages only on these
        [query] = [a for a in graphql if a.startswith("query=")]
        self.assertRegex(query, r"after:\s*\$endCursor")
        self.assertIn("pageInfo { hasNextPage endCursor }", query)
        self.assertIn("number=7", graphql)
        self.assertIn("owner=o", graphql)
        self.assertIn("repo=r", graphql)

    def test_a_deleted_author_is_not_a_bot(self):
        t = thread("A", "x")
        t["comments"]["nodes"][0]["author"] = None
        [out] = self.threads(page([t]))
        self.assertEqual((out["author"], out["bot"]), (None, False))

    def test_gh_repo_picks_the_repo_and_host(self):
        self.threads(page([]), env={"GH_REPO": "ghe.example.com/me/web"})
        [call] = self.gh.calls
        self.assertIn("owner=me", call["args"])
        self.assertIn("repo=web", call["args"])
        self.assertEqual(call["env"]["GH_HOST"], "ghe.example.com")

    def test_an_enterprise_checkout_queries_its_own_host(self):
        self.gh.rules.clear()
        self.gh.on("repo", "view", json={"url": "https://ghe.example.com/me/web"})
        self.threads(page([]))
        [graphql] = [c for c in self.gh.calls if c["args"][:2] == ["api", "graphql"]]
        self.assertIn("owner=me", graphql["args"])
        self.assertIn("repo=web", graphql["args"])
        self.assertEqual(graphql["env"]["GH_HOST"], "ghe.example.com")

    def test_gh_host_wins_over_the_checkout(self):
        self.threads(page([]), env={"GH_HOST": "ghe.example.com"})
        [graphql] = [c for c in self.gh.calls if c["args"][:2] == ["api", "graphql"]]
        self.assertEqual(graphql["env"]["GH_HOST"], "ghe.example.com")

    def test_an_unqualified_gh_repo_skips_the_checkout(self):
        self.threads(page([]), env={"GH_REPO": "me/web"})
        [call] = self.gh.calls
        self.assertIn("owner=me", call["args"])
        self.assertNotIn("GH_HOST", call["env"])

    def test_a_failed_query_fails_the_script(self):
        self.gh.on("api", "graphql", exit=1)
        self.assertNotEqual(self.gh.run(SCRIPT, 7).returncode, 0)

    def test_rejects_a_missing_pr_number(self):
        result = self.gh.run(SCRIPT)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.gh.calls, [])


if __name__ == "__main__":
    unittest.main()
