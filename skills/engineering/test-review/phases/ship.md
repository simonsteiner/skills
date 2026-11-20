# Ship phase

You check, review, and open the PR for one built candidate. Your brief gives the report path, the candidate ID, the branch and its base, the context rules, and the model rule for anything you spawn. Follow them.

Work from the card; don't reopen it. A card that proved wrong is a **Departure**: where the PR deliberately differs from the report, and why.

1. Check the diff (`git diff --stat <base>...`, then the hunks you need) against the approval bar below. Then call the Skill tool with "review-prs" in local mode: fixed point = the base branch, spec = the candidate's card. Rerun the checks.
2. Update the candidate's status row (`pr-open`, PR number) and the card's **After** (tests added or removed, mutations that turned new tests red, seconds saved, the Measure's new value), and write any Departure into the overview's **Departures**, including those the Build commits describe, in the same branch. Change nothing else in the report: it's a dated record.
3. Call the Skill tool with "conventional-commit" to commit, push, `gh pr create --base <base>`, and call the Skill tool with "pr-body" for the body, linking the card and showing each mutation that turned a new test red, or the before/after timings. **Never merge.**

## Approval bar

The PR isn't done while any of these hold, unless the report's Departures explain why:

- A new test that was never seen red: no mutation named, or it passes with the behaviour removed.
- A new test that mocks a module the project owns, reads private state, or asserts a value recomputed the way the code computes it.
- A new test at a seam the card didn't name, or at a lower level than the card said.
- A deleted test whose behaviour something relies on and nothing else guards, or a deleted test the card didn't list.
- Production code kept only for tests the PR deleted.
- Waste or infra without before/after numbers, or numbers that got worse.
- A skip, retry, or `.only` added, or a timeout raised to make a test pass.

**Hand back:** the PR number, its base, and the status row updated and pushed.
