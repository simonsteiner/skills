"""arch-review and test-review own copies of the same report-and-stack machinery
(docs/adr/0008-own-test-review-beside-arch-review.md). This guards the parts that
must not drift apart: the status values, the reconcile command, the shared
loose-ends checks, how a Ship phase ends, and that a `blocked` row stops its candidate.

    python3 -m unittest discover -s tests -t .
"""

import re
import unittest
from pathlib import Path

ENGINEERING = Path(__file__).resolve().parents[2] / "skills" / "engineering"
SKILLS = ("arch-review", "test-review")


def read(skill, path):
    return (ENGINEERING / skill / path).read_text()


def section(text, heading_pattern):
    """The text from the first heading matching the pattern to the next heading of any level."""
    match = re.search(rf"(?ms)^#+ {heading_pattern}.*?(?=^#+ |\Z)", text)
    return match.group(0) if match else ""


def status_values(skill):
    """The backticked values on the report template's `Status:` legend line."""
    line = re.search(r"(?m)^Status: (.*)$", read(skill, "assets/report-template.md"))
    return set(re.findall(r"`([a-z-]+)`", line.group(1))) if line else set()


LOOSE_ENDS_START = re.compile(r"\*\*Loose ends\.\*\*|## Step \d+ — Loose ends")
LOOSE_ENDS_END = "\nRunning low on budget"


def loose_ends(skill):
    """The loose-ends audit: from its heading to the "Running low on budget" line after it."""
    text = read(skill, "SKILL.md")
    start = LOOSE_ENDS_START.search(text)
    if not start:
        raise AssertionError(f"{skill}/SKILL.md has no loose-ends heading: neither **Loose ends.** "
                             "nor ## Step N — Loose ends")
    end = text.find(LOOSE_ENDS_END, start.end())
    if end < 0:
        raise AssertionError(f"{skill}/SKILL.md has no {LOOSE_ENDS_END.strip()!r} line after its "
                             f"{start.group(0)!r} heading, which ends the loose-ends audit")
    return text[start.start():end]


class ReviewSkillsAgreeTest(unittest.TestCase):
    def test_same_status_values(self):
        values = {s: status_values(s) for s in SKILLS}
        self.assertEqual(values["arch-review"], {"todo", "in-progress", "pr-open", "merged", "blocked", "dropped"})
        self.assertEqual(values["arch-review"], values["test-review"])

    def test_loose_ends_close_rows_on_the_same_terminal_statuses(self):
        for skill in SKILLS:
            line = re.search(r"Every batch row is ([^\n]*)", loose_ends(skill))
            self.assertIsNotNone(line, skill)
            terminal = set(re.findall(r"`([a-z-]+)`", line.group(1)))
            self.assertEqual(terminal, {"pr-open", "merged", "dropped", "blocked"}, skill)
            self.assertLessEqual(terminal, status_values(skill), skill)

    def test_same_reconcile_command(self):
        for skill in SKILLS:
            self.assertIn("gh pr list --state all --head <branch>", read(skill, "SKILL.md"), skill)

    def test_shared_loose_ends_checks(self):
        shared = ("`gh pr checks`", "branch below it", "status table matches `gh`", "`TODO`")
        for skill in SKILLS:
            audit = loose_ends(skill)
            for check in shared:
                self.assertIn(check, audit, f"{skill} loose ends lost {check}")

    def test_ship_phase_ends_the_same_way(self):
        for skill in SKILLS:
            ship = read(skill, "phases/ship.md")
            for step in ('"review-prs" in local mode', "gh pr create --base <base>", '"pr-body"', "Never merge"):
                self.assertIn(step, ship, f"{skill} ship phase lost {step}")
            self.assertTrue(section(ship, "Approval bar"), f"{skill} ship phase has no approval bar")

    def test_a_blocked_row_stops_its_candidate(self):
        for skill in SKILLS:
            self.assertRegex(read(skill, "SKILL.md"), r"handed back `blocked`[^.]*gets no", skill)
            self.assertIn("the row `blocked`", read(skill, "phases/design.md"), skill)
        self.assertIn("the row `blocked`", read("test-review", "phases/build.md"))

    def test_every_phase_brief_is_linked_and_carries_the_context_rules(self):
        for skill in SKILLS:
            text = read(skill, "SKILL.md")
            self.assertTrue(section(text, "Context rules"), skill)
            for phase in sorted((ENGINEERING / skill / "phases").glob("*.md")):
                self.assertIn(f"](phases/{phase.name})", text, f"{skill} never links {phase.name}")
                self.assertIn("context rules", phase.read_text(), f"{skill} {phase.name} skips the context rules")


if __name__ == "__main__":
    unittest.main()
