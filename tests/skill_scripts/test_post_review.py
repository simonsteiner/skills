"""Tests for skills/engineering/review-prs/scripts/post-review.sh, through a fake gh.

    python3 -m unittest discover -s tests -t .
"""

import json
import tempfile
import unittest
from pathlib import Path

from .fake_gh import FakeGh

SCRIPT = Path(__file__).resolve().parents[2] / "skills/engineering/review-prs/scripts/post-review.sh"
REVIEWS = "repos/{owner}/{repo}/pulls/7/reviews"
FILES = "repos/{owner}/{repo}/pulls/7/files?per_page=100"

# Line numbers per hunk, as GitHub's files API lists them (raw paths, a `patch` per file):
#   src/a.ts   old 100-103, new 10-12  (101-102 deleted, 11 added)
#              old 200-201, new 50-52  (a "+++ " line added inside the hunk is content, not a header)
#   new.ts     new 1-2 (added file; no old side)
#   gone.ts    old 1-2 (deleted file; no new side)
#   sp ace.ts, ümlaut.ts, ta<TAB>b.ts, x<CR>y.ts, x<LF>y.ts  line 1 or 5 both sides (paths git would quote)
#   renamed.ts (from old.ts)  old 10-11, new 10-11
#   data/t3.json  no `patch`: GitHub shows no diff for it (too large or generated)
# Two pages, as `--paginate` returns them.
FILES_PAGES = [
    [
        {"filename": "src/a.ts", "status": "modified",
         "patch": "@@ -100,4 +10,3 @@ function f() {\n keep\n-removed one\n-removed two\n+added\n keep\n"
                  "@@ -200,2 +50,3 @@\n keep\n++++ not/a/header\n keep"},
        {"filename": "new.ts", "status": "added", "patch": "@@ -0,0 +1,2 @@\n+x\n+y"},
        {"filename": "gone.ts", "status": "removed", "patch": "@@ -1,2 +0,0 @@\n-x\n-y"},
        {"filename": "sp ace.ts", "status": "modified", "patch": "@@ -5 +5 @@\n-old\n+new"},
        {"filename": "ümlaut.ts", "status": "modified", "patch": "@@ -1 +1 @@\n-old\n+new"},
    ],
    [
        {"filename": "renamed.ts", "previous_filename": "old.ts", "status": "renamed",
         "patch": "@@ -10,2 +10,2 @@\n keep\n-was\n+now"},
        {"filename": "x\ny.ts", "status": "modified", "patch": "@@ -1 +1 @@\n-old\n+new"},
        {"filename": "x\ry.ts", "status": "modified", "patch": "@@ -1 +1 @@\n-old\n+new"},
        {"filename": "ta\tb.ts", "status": "modified", "patch": "@@ -1 +1 @@\n-old\n+new"},
        {"filename": "data/t3.json", "status": "modified"},
    ],
]


def comment(path, line, **extra):
    return {"path": path, "line": line, "body": "**Bug** — x", **extra}


class PostReviewTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.gh = FakeGh(tmp.name)
        self.gh.on("api", FILES, "--paginate", pages=FILES_PAGES)
        self.gh.on("api", "user", json={"login": "me"})

    def post(self, *comments, body="1 finding."):
        return self.gh.run(SCRIPT, 7, stdin=json.dumps({"body": body, "comments": list(comments)}))

    def ready_to_post(self, posted=None, exit=0):
        self.gh.on("api", REVIEWS, "--paginate", json=[{"id": 1, "state": "PENDING", "user": {"login": "other"}}],
                   once=True)
        self.gh.on("pr", "view", "7", json={"headRefOid": "abc123"})
        self.gh.on("api", REVIEWS, "--input", json=posted or {"html_url": "https://x/r/1", "state": "COMMENTED"},
                   exit=exit)

    def posted(self):
        return [json.loads(c["stdin"]) for c in self.gh.calls if "--input" in c["args"]]

    def assert_outside(self, result, *where):
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stderr.splitlines()[1:], list(where))
        self.assertEqual(self.posted(), [])

    def assert_posts(self, *comments):
        self.ready_to_post()
        result = self.post(*comments)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "https://x/r/1 COMMENTED\n")
        [review] = self.posted()
        self.assertEqual((review["commit_id"], review["event"], review["comments"]), ("abc123", "COMMENT", list(comments)))

    # The payload

    def test_empty_or_invalid_payload_sends_nothing(self):
        for stdin in ("", "  \n", "not json", '{"body": ""}', '{"body": "x", "comments": {}}'):
            result = self.gh.run(SCRIPT, 7, stdin=stdin)
            self.assertEqual(result.returncode, 1, stdin)
            self.assertIn("nothing posted", result.stderr)
            self.assertEqual(self.gh.calls, [])

    def test_a_diff_too_big_for_argv_still_posts(self):
        # Replacing a vendored library once made jq die with "Argument list too long":
        # 10k hunks put the hunk list well past the 128 KiB one argument may hold.
        big = [[{"filename": f"vendor/lib/f{n}.cpp", "status": "added", "patch": "@@ -0,0 +1 @@\n+x"}
                for n in range(page * 100, page * 100 + 100)] for page in range(100)]
        self.gh.rules = [r for r in self.gh.rules if r["args"][:2] != ["api", FILES]]
        self.gh.on("api", FILES, "--paginate", pages=big)
        self.assert_posts(comment("vendor/lib/f9999.cpp", 1))

    def test_a_pr_too_big_for_gh_pr_diff_still_posts(self):
        # GitHub answers `gh pr diff` with HTTP 406 past 300 files or 20,000 lines, so a
        # 301-file PR could not be reviewed at all; the files API pages through it.
        big = [[{"filename": f"gen/f{n}.ts", "status": "added", "patch": "@@ -0,0 +1,100 @@\n" + "+x\n" * 100}
                for n in range(page * 100, min(page * 100 + 100, 301))] for page in range(4)]
        self.gh.rules = [r for r in self.gh.rules if r["args"][:2] != ["api", FILES]]
        self.gh.on("api", FILES, "--paginate", pages=big)
        self.gh.on("pr", "diff", "7", exit=1,
                   stdout="HTTP 406: Sorry, the diff exceeded the maximum number of files (300).")
        self.assert_posts(comment("gen/f300.ts", 100))
        self.assertFalse([c for c in self.gh.calls if c["args"][:2] == ["pr", "diff"]])

    def test_a_file_github_shows_no_diff_for_is_outside(self):
        # A large or generated file (data/t3.json) used to pass the `gh pr diff` check, then
        # GitHub rejected the whole review with 422 "Line could not be resolved".
        self.assert_outside(self.post(comment("data/t3.json", 1), comment("src/a.ts", 11)), "data/t3.json:1")

    def test_the_3000_file_cap_is_named_when_a_comment_is_outside(self):
        capped = [[{"filename": f"f{n}.ts", "status": "added", "patch": "@@ -0,0 +1 @@\n+x"}
                   for n in range(page * 100, page * 100 + 100)] for page in range(30)]
        self.gh.rules = [r for r in self.gh.rules if r["args"][:2] != ["api", FILES]]
        self.gh.on("api", FILES, "--paginate", pages=capped)
        result = self.post(comment("f3000.ts", 1))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("f3000.ts:1", result.stderr)
        self.assertIn("only the first 3000 files", result.stderr)
        self.assertEqual(self.posted(), [])

    def test_pr_must_be_a_number(self):
        self.assertEqual(self.gh.run(SCRIPT, "x", stdin="{}").returncode, 1)

    # New-file lines (side RIGHT, the default)

    def test_summary_without_comments_posts(self):
        self.assert_posts()

    def test_right_lines_inside_a_hunk_post(self):
        self.assert_posts(comment("src/a.ts", 11, side="RIGHT"), comment("src/a.ts", 52),
                          comment("src/a.ts", 11, start_line=10, side="RIGHT"), comment("new.ts", 2))

    def test_right_lines_outside_every_hunk_are_listed(self):
        self.assert_outside(self.post(comment("src/a.ts", 13), comment("src/a.ts", 49, side="RIGHT"),
                                      comment("other.ts", 1)),
                            "src/a.ts:13", "src/a.ts:49", "other.ts:1")

    def test_a_range_must_sit_in_one_hunk(self):
        self.assert_outside(self.post(comment("src/a.ts", 50, start_line=12)), "src/a.ts:12-50")

    def test_a_plus_line_inside_a_hunk_is_not_a_file_header(self):
        # 9f91a46: "++++ not/a/header" was read as a new path, so line 51 fell outside.
        self.assert_posts(comment("src/a.ts", 51))

    def test_paths_git_would_quote_match_as_they_are(self):
        self.assert_posts(comment("sp ace.ts", 5), comment("ümlaut.ts", 1), comment("ta\tb.ts", 1, side="LEFT"),
                          comment("x\ry.ts", 1), comment("x\ny.ts", 1))

    def test_paths_match_exactly(self):
        self.assert_outside(self.post(comment("sp ace.ts\t", 5), comment("a.ts", 11)), "sp ace.ts\t:5", "a.ts:11")

    def test_a_renamed_file_is_addressed_by_its_new_path_on_both_sides(self):
        self.assert_posts(comment("renamed.ts", 11, side="LEFT"),
                          comment("renamed.ts", 11, start_line=11, start_side="LEFT", side="RIGHT"))

    def test_a_renamed_file_has_no_comments_under_its_old_path(self):
        self.assert_outside(self.post(comment("old.ts", 11, side="LEFT")), "old.ts:11")

    # Old-file lines (side LEFT)

    def test_left_lines_inside_a_hunk_post(self):
        self.assert_posts(comment("src/a.ts", 101, side="LEFT"),
                          comment("src/a.ts", 102, start_line=100, side="LEFT"),
                          comment("gone.ts", 2, side="LEFT"))

    def test_left_lines_are_old_file_numbers(self):
        # Line 11 is inside the new side of the first hunk but not the old one (100-103):
        # GitHub would reject the whole review.
        self.assert_outside(self.post(comment("src/a.ts", 11, side="LEFT"), comment("new.ts", 1, side="LEFT")),
                            "src/a.ts:11", "new.ts:1")

    def test_a_range_can_start_on_the_old_side(self):
        self.assert_posts(comment("src/a.ts", 11, start_line=101, start_side="LEFT", side="RIGHT"))

    def test_a_range_across_two_hunks_is_outside(self):
        self.assert_outside(self.post(comment("src/a.ts", 50, start_line=101, start_side="LEFT", side="RIGHT")),
                            "src/a.ts:101-50")

    # Drafts

    def test_refuses_while_you_have_a_draft(self):
        self.gh.on("api", REVIEWS, "--paginate", json=[{"id": 5, "state": "PENDING", "user": {"login": "me"}}])
        result = self.post(comment("src/a.ts", 11))
        self.assertEqual(result.returncode, 1)
        self.assertIn("already have a pending draft review on PR 7 (id 5)", result.stderr)
        self.assertEqual(self.posted(), [])

    def test_a_failed_post_deletes_only_the_draft_it_created(self):
        # 036eda2: the other user's draft (id 1) must survive; the new one (id 9) goes.
        self.ready_to_post(exit=1)
        self.gh.on("api", REVIEWS, "--paginate", json=[{"id": 1, "state": "PENDING", "user": {"login": "other"}},
                                                       {"id": 9, "state": "PENDING", "user": {"login": "me"}}])
        self.gh.on("api", "-X", "DELETE", f"{REVIEWS}/9")
        result = self.post(comment("src/a.ts", 11))
        self.assertEqual(result.returncode, 1)
        self.assertIn("deleted pending review 9", result.stderr)
        deletes = [c["args"] for c in self.gh.calls if "DELETE" in c["args"]]
        self.assertEqual(deletes, [["api", "-X", "DELETE", f"{REVIEWS}/9"]])


if __name__ == "__main__":
    unittest.main()
