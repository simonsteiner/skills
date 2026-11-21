# Ship phase

You check, review, and open the PR for one built candidate. Your brief gives the report path, the candidate ID, the branch and its base, the context rules, and the model rule for anything you spawn. Follow them.

Work from the candidate's card and its Decisions; don't reopen the design. A Decision that proved wrong is a **Departure**: where the PR deliberately differs from the report, and why.

1. Check the diff (`git diff --stat <base>...`, then the hunks you need) against the approval bar below. Then call the Skill tool with "review-prs" in local mode: fixed point = the base branch, spec = this candidate's card and its Decisions. It fixes what's real; rerun the checks.
2. Write any Departure into the overview's **Departures**, including those the Build commits describe, in the same branch. Call the Skill tool with "conventional-commit" to commit, push, then `gh pr create --base <base>`. Call the Skill tool with "pr-body" for the body, and link the candidate's card file from it. Use codebase-design's terms (module, interface, seam, depth, locality) in both. **Never merge.**
3. Now that the PR exists, update the candidate's status row (`pr-open`, PR number, Breaking), commit, and push. Change nothing else in the report: it's a dated record.

## Approval bar

The PR isn't done while any of these hold, unless the report's Departures explain why:

- A visible path to delete complexity was left unused; complexity moved rather than shrank.
- A file crossed the project's token budget (or 1,000 lines, without one) because of this PR.
- New ad-hoc branching in an existing flow, or feature checks scattered through shared code.
- A new pass-through module, a single-adapter seam, or a cast-heavy interface.
- A near-duplicate of an existing helper, or logic placed outside the module that owns the concept.
- Old tests and shallow modules kept beside their replacement.
- A change that should land in one place still needs several: pieces that change together stay apart, or a new import points at a module more volatile than the importer.

**Hand back:** the PR number, its base, and the status row updated and pushed.
