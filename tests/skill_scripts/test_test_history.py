"""Tests for skills/engineering/test-review/scripts/test-history.py, against throwaway repos.

    python3 -m unittest discover -s tests -t .
"""

import os
import re
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/engineering/test-review/scripts/test-history.py"

# A git hook running the suite exports GIT_DIR, GIT_INDEX_FILE, …; they'd point every call at the outer repo.
ENV = {**{k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}

# inside the default --since window, so only an honoured --since drops it
def days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%dT12:00:00")


class TestHistoryTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.git("init", "-q")
        self.n = 0

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, env=ENV, capture_output=True, text=True, check=True)

    def commit(self, subject, *paths, date=None):
        self.n += 1
        for path in paths:
            f = self.repo / path
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"{self.n}\n")
        self.git("add", "-A")
        dates = {} if date is None else {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
        subprocess.run(["git", "commit", "-q", "-m", subject], cwd=self.repo, env={**ENV, **dates},
                       capture_output=True, check=True)
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

    def test_drift_pairs_a_test_beside_an_index_or_main_file_by_either_name(self):
        for _ in range(3):
            self.commit("feat: x", "src/utils/index.ts", "src/utils/index.test.ts",
                        "cmd/tool/main.go", "cmd/tool/main_test.go")
        got = {row[3]: (row[1], row[4]) for row in self.rows("drift")}
        self.assertEqual(got, {"src/utils/index.ts": ("100%", "src/utils/index.test.ts"),
                               "cmd/tool/main.go": ("100%", "cmd/tool/main_test.go")})

    def test_drift_rounds_shares_half_up(self):
        for i in range(8):
            self.commit("feat: x", "a.py", *(["tests/test_a.py"] if i < 5 else []))
        self.assertEqual(self.rows("drift"), [["8", "63%", "63%", "a.py", "tests/test_a.py"]])

    def test_drift_keeps_non_ascii_and_spaced_paths(self):
        for _ in range(3):
            self.commit("feat: x", "src/größe.py", "src/my module.py")
        self.assertEqual(sorted(r[3] for r in self.rows("drift")), ["src/größe.py", "src/my module.py"])

    def test_drift_scope_is_relative_to_the_current_directory_and_top_caps_rows(self):
        for _ in range(4):
            self.commit("feat: x", "pkg/api/route.py", "pkg/api/auth.py", "web/page.py")
        result = self.run_script("drift", "api", cwd=self.repo / "pkg")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([line.split("\t")[3] for line in result.stdout.splitlines()],
                         ["pkg/api/auth.py", "pkg/api/route.py"])
        self.assertEqual(len(self.rows("drift", "--top", "1")), 1)

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

    def test_drift_pairs_only_test_code_not_fixtures(self):
        self.commit("feat: a", "src/cart.py", "tests/test_cart.py")
        for i in range(3):
            self.commit(f"feat: {i}", "src/cart.py", "tests/fixtures/cart.json")
        self.assertEqual(self.rows("drift"), [["4", "25%", "100%", "src/cart.py", "tests/test_cart.py"]])

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
        self.commit("Add debug panel and fixtures", "src/panel.py")
        self.assertEqual(self.lines("fixes"), ["# 0 of 0 fix commits changed no test"])

    def test_a_conventional_type_decides_over_the_words_and_reverts_count_as_neither(self):
        self.commit("chore: fix lint warnings", "src/a.py")
        self.commit('Revert "fix: round totals"', "src/a.py")
        self.commit("feat(pdf): extract tables", "src/pdf.py", "tests/test_pdf.py")
        self.commit("feat: let users rename files", "src/files.py", "tests/test_pdf.py")
        bugfix = self.commit("Bugfix for login", "src/login.py")
        typed = self.commit("Fix(auth)!: drop the legacy token", "src/auth.py")
        self.assertEqual([r[0] for r in self.rows("fixes")], [typed, bugfix])
        self.assertEqual(self.lines("refactors"), ["# 0 of 0 refactor commits changed a test"])

    def test_a_component_prefix_is_not_a_type(self):
        crash = self.commit("parser: fix crash on empty input", "src/parser.py")
        self.commit("README: fix typo", "README.md")
        extract = self.commit("api: extract client", "src/api.py", "tests/test_api.py")
        self.assertEqual([r[0] for r in self.rows("fixes")], [crash])
        self.assertEqual(self.rows("refactors", "--min", "1"), [["1", "tests/test_api.py", extract]])

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

    def test_refactors_counts_only_commits_touching_a_source_in_scope(self):
        a = self.commit("refactor: split cart", "src/cart.py", "tests/test_cart.py")
        self.commit("refactor: split admin", "admin/panel.py", "tests/test_cart.py")
        self.assertEqual(self.rows("refactors", "--min", "1", "src"), [["1", "tests/test_cart.py", a]])
        self.assertEqual(self.lines("refactors", "src")[-1], "# 1 of 1 refactor commits changed a test")

    # shared

    def test_since_bounds_the_history(self):
        self.commit("fix: old", "src/old.py", date=days_ago(30))
        new = self.commit("fix: new", "src/new.py")
        self.assertEqual([r[0] for r in self.rows("fixes", "--since", days_ago(10)[:10])], [new])

    def test_sweeping_commits_are_skipped(self):
        for _ in range(3):
            self.commit("fix: sweep", "a.py", "b.py", "c.py")
        self.assertEqual(self.rows("drift", "--max-files", "2"), [])
        self.assertEqual(self.lines("fixes", "--max-files", "2"), ["# 0 of 0 fix commits changed no test"])

    def test_empty_repo_prints_no_rows_but_still_the_summary(self):
        self.assertEqual(self.lines("drift"), [])
        self.assertEqual(self.lines("fixes"), ["# 0 of 0 fix commits changed no test"])
        self.assertEqual(self.lines("refactors"), ["# 0 of 0 refactor commits changed a test"])

    def test_names_git_quotes_are_kept(self):
        # a tab or newline in a name splits its row, so look for each row in the raw output
        for name in ('say "hi"', "back\\slash", "tab\tname", "new\nline"):
            with self.subTest(name=name):
                for i in range(3):
                    self.commit(f"feat: {i}", f"src/{name}.py", f"tests/test_{name}.py")
                drift = self.run_script("drift").stdout
                self.assertIn(f"3\t100%\t100%\tsrc/{name}.py\ttests/test_{name}.py\n", drift)
                fix = self.commit("fix: quoted", f"src/{name}.py")
                fixes = self.run_script("fixes").stdout
                self.assertRegex(fixes, f"^{fix}\t[0-9-]+\tfix: quoted\tsrc/{re.escape(name)}\\.py\n")

    def test_negative_counts_exit_2(self):
        self.commit("feat: a", "a.py")
        for flag in ("--top", "--min", "--max-files"):
            with self.subTest(flag=flag):
                result = self.run_script("drift", flag, "-1")
                self.assertEqual(result.returncode, 2)
                self.assertIn(flag, result.stderr)

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
