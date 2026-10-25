"""Tests for skills/engineering/review-prs/scripts/outside-findings.sh, through a fake gh.

    python3 -m unittest discover -s tests -t .
"""

import json
import tempfile
import unittest
from pathlib import Path

from .fake_gh import FakeGh

SCRIPT = Path(__file__).resolve().parents[2] / "skills/engineering/review-prs/scripts/outside-findings.sh"
RUNS = "repos/{owner}/{repo}/commits/abc123/check-runs?per_page=100"


def run(id, name, count):
    return {"id": id, "name": name, "output": {"annotations_count": count}}


def annotation(path, line, level="warning", title="t", message="m"):
    return {"path": path, "start_line": line, "end_line": line, "annotation_level": level,
            "title": title, "message": message}


class OutsideFindingsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.gh = FakeGh(tmp.name)
        self.gh.on("pr", "view", "7", json={"headRefOid": "abc123"})

    def findings(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        return [json.loads(line) for line in result.stdout.splitlines()]

    def test_lists_annotations_of_every_annotated_run_with_its_name(self):
        self.gh.on("api", RUNS, "--paginate", pages=[
            {"check_runs": [run(1, "lint", 2), run(2, "tests", 0)]},
            {"check_runs": [run(3, "CodeQL", 1)]},
        ])
        self.gh.on("api", "repos/{owner}/{repo}/check-runs/1/annotations?per_page=100", "--paginate",
                   pages=[[annotation("src/a.ts", 12)], [annotation("src/b.ts", 3, "failure")]])
        self.gh.on("api", "repos/{owner}/{repo}/check-runs/3/annotations?per_page=100", "--paginate",
                   json=[annotation("src/c.ts", 40, "failure", "SQL injection", "user input reaches query")])
        self.assertEqual(self.findings(self.gh.run(SCRIPT, 7)), [
            {"source": "lint", "path": "src/a.ts", "line": 12, "end_line": 12, "level": "warning", "title": "t", "message": "m"},
            {"source": "lint", "path": "src/b.ts", "line": 3, "end_line": 3, "level": "failure", "title": "t", "message": "m"},
            {"source": "CodeQL", "path": "src/c.ts", "line": 40, "end_line": 40, "level": "failure",
             "title": "SQL injection", "message": "user input reaches query"},
        ])
        self.assertFalse(any("check-runs/2/" in c["args"][1] for c in self.gh.calls))

    def test_drops_the_runners_own_notices(self):
        self.gh.on("api", RUNS, "--paginate", json={"check_runs": [run(1, "build", 2)]})
        self.gh.on("api", "repos/{owner}/{repo}/check-runs/1/annotations?per_page=100", "--paginate",
                   json=[annotation(".github", 1, "notice"), annotation("src/a.ts", 5)])
        self.assertEqual([f["path"] for f in self.findings(self.gh.run(SCRIPT, 7))], ["src/a.ts"])

    def test_no_annotated_runs_prints_nothing(self):
        self.gh.on("api", RUNS, "--paginate", json={"check_runs": [run(1, "tests", 0)]})
        self.assertEqual(self.findings(self.gh.run(SCRIPT, 7)), [])

    def test_a_failed_gh_call_fails_the_script(self):
        self.gh.on("api", RUNS, "--paginate", json={"check_runs": [run(1, "lint", 1)]})
        self.gh.on("api", "repos/{owner}/{repo}/check-runs/1/annotations?per_page=100", "--paginate", exit=1)
        self.assertNotEqual(self.gh.run(SCRIPT, 7).returncode, 0)

    def test_rejects_a_missing_pr_number(self):
        result = self.gh.run(SCRIPT)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.gh.calls, [])


if __name__ == "__main__":
    unittest.main()
