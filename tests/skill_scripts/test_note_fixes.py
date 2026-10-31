"""Tests for skills/engineering/review-prs/scripts/note-fixes.sh, through a fake gh.

    python3 -m unittest discover -s tests -t .
"""

import json
import tempfile
import unittest
from pathlib import Path

from .fake_gh import FakeGh

SCRIPT = Path(__file__).resolve().parents[2] / "skills/engineering/review-prs/scripts/note-fixes.sh"
REVIEW = "repos/{owner}/{repo}/pulls/7/reviews/42"
SUMMARY = "2 findings (1 Bug, 1 Nit).\n\n**Checks.** Tests pass.\n\nRange: d411b7e..8f6d7e4"


class NoteFixesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.gh = FakeGh(tmp.name)

    def run_with(self, body, *shas):
        self.gh.on("api", REVIEW, "--jq", ".body", json={"body": body})
        self.gh.on("api", "-X", "PUT", REVIEW, json={"html_url": "https://github.com/o/r/pull/7#pullrequestreview-42"})
        return self.gh.run(SCRIPT, 7, 42, *shas)

    def sent_body(self):
        [put] = [c for c in self.gh.calls if c["args"][:2] == ["api", "-X"]]
        return json.loads(put["stdin"])["body"]

    def test_adds_a_fixed_line_after_the_range(self):
        result = self.run_with(SUMMARY, "0de7231", "2abf15e")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "https://github.com/o/r/pull/7#pullrequestreview-42")
        self.assertEqual(self.sent_body(), SUMMARY + "\nFixed: 0de7231 2abf15e")

    def test_a_second_round_extends_the_same_line_without_duplicates(self):
        body = "Summary.\n\nRange: d411b7e..8f6d7e4\nFixed: 0de7231 2abf15e\n\nTrailing note."
        self.assertEqual(self.run_with(body, "2abf15e", "6716559").returncode, 0)
        self.assertEqual(self.sent_body(),
                         "Summary.\n\nRange: d411b7e..8f6d7e4\nFixed: 0de7231 2abf15e 6716559\n\nTrailing note.")

    def test_refuses_a_review_without_a_range_line(self):
        result = self.run_with("LGTM, nice work.", "0de7231")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a review-prs summary", result.stderr)
        self.assertNotIn(["api", "-X"], [c["args"][:2] for c in self.gh.calls])

    def test_refuses_bad_arguments_without_calling_gh(self):
        for args in [(7, 42), ("x", 42, "0de7231"), (7, "y", "0de7231"), (7, 42, "main"), (7, 42, "0de72")]:
            with self.subTest(args=args):
                self.assertEqual(self.gh.run(SCRIPT, *args).returncode, 1)
                self.assertEqual(self.gh.calls, [])


if __name__ == "__main__":
    unittest.main()
