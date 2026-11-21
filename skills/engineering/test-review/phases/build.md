# Build phase

You fix one candidate whose card the user already confirmed. Your brief gives the report path, the candidate ID, the branch and its base, the context rules, and the model rule for anything you spawn. Follow them.

Work from the card: its kind (blind spot, waste, infra) decides the route. A card that proves wrong becomes a **Departure**, not a redesign: do what works, and say in the commit body what differs from the card and why, so the Ship phase can write it into the report. Use codebase-design's terms (module, interface, seam, adapter) and prune-tests' (a test guards a behaviour, or depends on the past, on nothing, or on the implementation) in commits.

Branch the planned name off the base, or check out the Design phase's branch for an `infra` row. A batch of smaller findings has no Design phase: cut `test/smaller-findings-<n>` off the base. A `one-way` row (the card's door) stops before the change that crosses the door: mark it `blocked` with the question in Notes, commit the row, and hand back. Then by kind:

- **Blind spot.** Call the Skill tool with "tdd". The seams are the card's, already confirmed by the user at the batch checkpoint; don't ask again. Pin one behaviour per cycle, through the seam's public interface, mocking only at system boundaries. Existing code usually passes a new test at once, so **prove each test can fail**: make the smallest change to the code under test that breaks the behaviour, watch the test go red, revert, and name that mutation in the commit body. A test that's red against the unchanged code found a live defect: keep it, fix the code in this PR, mark the row 🔴, and call the Skill tool with "diagnosing-bugs" when the cause isn't plain from the failure.
- **Waste.** Time the affected tests first. Call the Skill tool with "prune-tests", passing each file that holds the card's Prune rows. It takes only a path and prunes every test in it, but only the card's rows were confirmed: commit the changes to those rows alone, put back every other test it cut or rewrote, and make each of those a new `S` row in the status table, not part of this PR. Before each deletion, the card says what still guards the behaviour; a test that's the only guard of a behaviour something relies on is rewritten against that behaviour, not deleted. Time them again.
- **Infra.** Implement the Decisions: hooks through the Skill tool with "setup-lefthook", workflows through the Skill tool with "secure-github-actions". Re-measure what the card said it should move (suite time, single-file time, reruns, an order-shuffled run passing).

Then run what the repo runs — typecheck, lint, the full suite — and call the Skill tool with "conventional-commit" to commit.

**Hand back:** the branch committed with checks green and the before/after numbers, the row `blocked` with its question, or what failed and the trimmed output that shows it.
