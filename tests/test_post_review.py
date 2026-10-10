"""Tests for skills/engineering/review-prs/scripts/post-review.sh, through a fake gh.

    python3 -m unittest discover -s tests
"""

import json
import tempfile
import unittest
from pathlib import Path

from fake_gh import FakeGh

SCRIPT = Path(__file__).resolve().parent.parent / "skills/engineering/review-prs/scripts/post-review.sh"
REVIEWS = "repos/{owner}/{repo}/pulls/7/reviews"

# Line numbers per hunk:
#   src/a.ts   old 100-103, new 10-12  (101-102 deleted, 11 added)
#              old 200-201, new 50-52  (a "+++ " line added inside the hunk is content, not a header)
#   new.ts     new 1-2 (added file; no old side)
#   gone.ts    old 1-2 (deleted file; no new side)
#   sp ace.ts  line 5 both sides (git ends a header path holding a space with a tab)
#   ümlaut.ts, ta<TAB>b.ts, x<CR>y.ts, x<LF>y.ts  line 1 both sides (git C-quotes these, octal for non-ASCII)
#   renamed.ts (from old.ts)  old 10-11, new 10-11
DIFF = """\
diff --git a/src/a.ts b/src/a.ts
index 1111111..2222222 100644
--- a/src/a.ts
+++ b/src/a.ts
@@ -100,4 +10,3 @@ function f() {
 keep
-removed one
-removed two
+added
 keep
@@ -200,2 +50,3 @@
 keep
++++ not/a/header
 keep
diff --git a/new.ts b/new.ts
new file mode 100644
--- /dev/null
+++ b/new.ts
@@ -0,0 +1,2 @@
+x
+y
diff --git a/gone.ts b/gone.ts
deleted file mode 100644
--- a/gone.ts
+++ /dev/null
@@ -1,2 +0,0 @@
-x
-y
diff --git a/sp ace.ts b/sp ace.ts
--- a/sp ace.ts\t
+++ b/sp ace.ts\t
@@ -5 +5 @@
-old
+new
diff --git "a/\\303\\274mlaut.ts" "b/\\303\\274mlaut.ts"
--- "a/\\303\\274mlaut.ts"
+++ "b/\\303\\274mlaut.ts"
@@ -1 +1 @@
-old
+new
diff --git a/old.ts b/renamed.ts
similarity index 80%
rename from old.ts
rename to renamed.ts
--- a/old.ts
+++ b/renamed.ts
@@ -10,2 +10,2 @@
 keep
-was
+now
diff --git "a/x\\ny.ts" "b/x\\ny.ts"
--- "a/x\\ny.ts"
+++ "b/x\\ny.ts"
@@ -1 +1 @@
-old
+new
diff --git "a/x\\ry.ts" "b/x\\ry.ts"
--- "a/x\\ry.ts"
+++ "b/x\\ry.ts"
@@ -1 +1 @@
-old
+new
diff --git "a/ta\\tb.ts" "b/ta\\tb.ts"
--- "a/ta\\tb.ts"
+++ "b/ta\\tb.ts"
@@ -1 +1 @@
-old
+new
"""


def comment(path, line, **extra):
    return {"path": path, "line": line, "body": "**Bug** — x", **extra}


class PostReviewTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.gh = FakeGh(tmp.name)
        self.gh.on("pr", "diff", "7", stdout=DIFF)
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

    def test_paths_as_git_writes_them(self):
        self.assert_posts(comment("sp ace.ts", 5), comment("ümlaut.ts", 1), comment("ta\tb.ts", 1, side="LEFT"),
                          comment("x\ry.ts", 1))

    def test_a_path_with_a_newline_reads_as_outside_not_as_a_crash(self):
        result = self.post(comment("x\ny.ts", 1))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(self.posted(), [])

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
