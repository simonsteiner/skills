"""Tests for skills/engineering/test-review/scripts/test-history.py, against throwaway repos.

    python3 -m unittest discover -s tests -t .
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/engineering/test-review/scripts/test-history.py"

# A git hook running the suite exports GIT_DIR, GIT_INDEX_FILE, …; they'd point every call at the outer repo.
ENV = {**{k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}


class TestHistoryTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.git("init", "-q")
        self.n = 0

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, env=ENV, capture_output=True, text=True, check=True)

    def commit(self, subject, *paths):
        self.n += 1
        for path in paths:
            f = self.repo / path
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"{self.n}\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", subject)
        return self.git("rev-parse", "--short", "HEAD").stdout.strip()

    def run_script(self, *args, cwd=None):
        return subprocess.run([str(SCRIPT), *args], cwd=cwd or self.repo, env=ENV,
                              capture_output=True, text=True, check=False)

    def lines(self, *args):
        result = self.run_script(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.splitlines()

    def rows(self, *args):
        return [line.split("\t") for line in self.lines(*args) if not line.startswith("#")]

    # drift

    def test_drift_shares_count_commits_that_also_changed_own_and_any_tests(self):
        self.commit("feat: a", "src/cart.py", "tests/test_cart.py")
        self.commit("feat: b", "src/cart.py", "tests/test_other.py")
        self.commit("feat: c", "src/cart.py")
        self.commit("feat: d", "src/cart.py")
        self.assertEqual(self.rows("drift"), [["4", "25%", "50%", "src/cart.py", "tests/test_cart.py"]])

    def test_drift_marks_a_source_with_no_own_test(self):
        for i in range(3):
            self.commit(f"feat: {i}", "lib/pricing.ts")
        self.assertEqual(self.rows("drift"), [["3", "-", "0%", "lib/pricing.ts", "-"]])

    def test_drift_pairs_tests_across_naming_conventions(self):
        cases = {"src/a/order.ts": "src/a/order.test.ts", "pkg/parse.go": "pkg/parse_test.go",
                 "src/Main/Invoice.java": "src/Main/InvoiceTest.java", "app/user.rb": "spec/user_spec.rb",
                 "web/button.jsx": "web/__tests__/button.spec.jsx", "src/report/index.ts": "test/report.test.ts"}
        for _ in range(3):
            for source, test in cases.items():
                self.commit("feat: x", source, test)
        got = {row[3]: (row[1], row[4]) for row in self.rows("drift")}
        self.assertEqual(got, {source: ("100%", test) for source, test in cases.items()})

    def test_drift_ranks_by_commits_and_drops_files_under_min_or_gone(self):
        for _ in range(4):
            self.commit("feat: a", "a.py")
        for _ in range(3):
            self.commit("feat: b", "b.py", "gone.py")
        self.commit("feat: c", "c.py")
        self.git("rm", "-q", "gone.py")
        self.git("commit", "-q", "-m", "chore: drop")
        self.assertEqual([r[3] for r in self.rows("drift")], ["a.py", "b.py"])

    def test_drift_ignores_docs_and_counts_extra_test_patterns(self):
        for _ in range(3):
            self.commit("docs: x", "README.md", "src/core.py", "checks/core_check.py")
        self.assertEqual([r[3] for r in self.rows("drift")], ["checks/core_check.py", "src/core.py"])
        self.assertEqual(self.rows("drift", "--test-pattern", r"^checks/"), [["3", "-", "100%", "src/core.py", "-"]])

    def test_drift_scopes_sources_to_paths_but_counts_tests_anywhere(self):
        for _ in range(3):
            self.commit("feat: x", "api/route.py", "web/page.py", "tests/test_route.py")
        self.assertEqual(self.rows("drift", "api"), [["3", "100%", "100%", "api/route.py", "tests/test_route.py"]])

    # fixes

    def test_fixes_lists_fix_commits_without_a_test_newest_first(self):
        self.commit("fix(cart): round totals", "src/cart.py", "tests/test_cart.py")
        old = self.commit("Fixes the login bug", "src/login.py")
        self.commit("feat: add prefix handling", "src/prefix.py")
        self.commit("fix: typo in docs", "README.md")
        new = self.commit("hotfix: null user", "src/user.py", "src/login.py")
        rows = self.rows("fixes")
        self.assertEqual([(r[0], r[2], r[3]) for r in rows],
                         [(new, "hotfix: null user", "src/login.py,src/user.py"),
                          (old, "Fixes the login bug", "src/login.py")])
        self.assertEqual(self.lines("fixes")[-1], "# 2 of 3 fix commits changed no test")

    def test_fixes_does_not_take_words_that_only_contain_fix_or_bug(self):
        self.commit("feat: debug panel and fixtures", "src/panel.py")
        self.assertEqual(self.lines("fixes"), ["# 0 of 0 fix commits changed no test"])

    # refactors

    def test_refactors_counts_test_files_changed_by_refactor_commits(self):
        a = self.commit("refactor: split cart", "src/cart.py", "tests/test_cart.py")
        b = self.commit("Rename helpers", "src/cart.py", "tests/test_cart.py", "tests/test_util.py")
        self.commit("refactor(api): extract client", "src/api.py")
        self.commit("feat: new cart rule", "src/cart.py", "tests/test_cart.py")
        self.assertEqual(self.rows("refactors"), [["2", "tests/test_cart.py", f"{b},{a}"]])
        self.assertEqual(self.rows("refactors", "--min", "1"),
                         [["2", "tests/test_cart.py", f"{b},{a}"], ["1", "tests/test_util.py", b]])
        self.assertEqual(self.lines("refactors")[-1], "# 2 of 3 refactor commits changed a test")

    # shared

    def test_sweeping_commits_are_skipped(self):
        for _ in range(3):
            self.commit("fix: sweep", "a.py", "b.py", "c.py")
        self.assertEqual(self.rows("drift", "--max-files", "2"), [])
        self.assertEqual(self.lines("fixes", "--max-files", "2"), ["# 0 of 0 fix commits changed no test"])

    def test_empty_repo_prints_nothing(self):
        self.assertEqual(self.lines("drift"), [])

    def test_bad_usage_exits_2(self):
        self.commit("feat: a", "a.py")
        for args in (["nope"], ["drift", "--since", "$(rm -rf /)"], ["drift", "--test-pattern", "("],
                     ["drift", "/"]):
            with self.subTest(args=args):
                self.assertEqual(self.run_script(*args).returncode, 2)

    def test_outside_a_repo_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_script("drift", cwd=tmp)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not inside a git repository", result.stderr)


if __name__ == "__main__":
    unittest.main()
