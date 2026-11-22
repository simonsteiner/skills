"""reply-resolve.sh replies in a review thread and resolves it only after a reply.

Run at its command, against the fake `gh`: what it refuses, which mutations it sends and in
what order, what it prints.

    uv run --locked --no-build python3 -m unittest tests.skill_scripts.test_reply_resolve
"""

import tempfile
import unittest
from pathlib import Path

from .fake_gh import FakeGh

SCRIPT = Path(__file__).resolve().parents[2] / "skills/engineering/address-review-findings/scripts/reply-resolve.sh"
THREAD = "PRRT_abc"
BODY = "Fixed in abc1234."
REPLY_URL = "https://github.com/acme/web/pull/7#discussion_r1"
REPLIED = {"data": {"addPullRequestReviewThreadReply": {"comment": {"url": REPLY_URL}}}}


def resolved(is_resolved):
    return {"data": {"resolveReviewThread": {"thread": {"isResolved": is_resolved}}}}


def mutations(calls):
    """Each logged graphql call as ("reply" | "resolve", the argv it carried)."""
    kinds = {"addPullRequestReviewThreadReply": "reply", "resolveReviewThread": "resolve"}
    out = []
    for call in calls:
        query = next(a for a in call["args"] if a.startswith("query="))
        out.append((next(kind for name, kind in kinds.items() if name in query), call["args"]))
    return out


class ReplyResolveTest(unittest.TestCase):
    def run_script(self, *args, stdin=BODY, is_resolved=True):
        with tempfile.TemporaryDirectory() as tmp:
            gh = FakeGh(tmp)
            gh.on("api", "graphql", "-f", f"threadId={THREAD}", "-f", f"body={stdin}", json=REPLIED)
            gh.on("api", "graphql", "-f", f"threadId={THREAD}", json=resolved(is_resolved))
            result = gh.run(SCRIPT, *args, stdin=stdin, env={"GH_REPO": "acme/web"}, cwd=tmp)
            return result, gh.calls

    def test_empty_body_exits_1_and_sends_nothing(self):
        for stdin in ("", "  \n\t\n"):
            with self.subTest(stdin=stdin):
                result, calls = self.run_script(THREAD, "--resolve", stdin=stdin)
                self.assertEqual(result.returncode, 1)
                self.assertIn("empty reply body", result.stderr)
                self.assertEqual(calls, [])

    def test_thread_id_not_starting_prrt_exits_1_and_sends_nothing(self):
        result, calls = self.run_script("PRRC_abc")
        self.assertEqual(result.returncode, 1)
        self.assertIn("PRRT_", result.stderr)
        self.assertEqual(calls, [])

    def test_unknown_second_argument_exits_1_and_sends_nothing(self):
        result, calls = self.run_script(THREAD, "--done")
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown option '--done'", result.stderr)
        self.assertEqual(calls, [])

    def test_reply_alone_sends_the_body_and_prints_the_url(self):
        result, calls = self.run_script(THREAD)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, REPLY_URL + "\n")
        sent = mutations(calls)
        self.assertEqual([kind for kind, _ in sent], ["reply"])
        self.assertIn(f"body={BODY}", sent[0][1])
        self.assertIn(f"threadId={THREAD}", sent[0][1])

    def test_resolve_follows_the_reply_and_prints_resolved(self):
        result, calls = self.run_script(THREAD, "--resolve")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, REPLY_URL + "\nresolved\n")
        sent = mutations(calls)
        self.assertEqual([kind for kind, _ in sent], ["reply", "resolve"])
        self.assertIn(f"threadId={THREAD}", sent[1][1])

    def test_thread_that_stays_unresolved_fails(self):
        result, calls = self.run_script(THREAD, "--resolve", is_resolved=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("resolved", result.stdout)
        self.assertEqual([kind for kind, _ in mutations(calls)], ["reply", "resolve"])
