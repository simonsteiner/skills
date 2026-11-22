# Review lenses

Read in Step 2. Each lens lists only what the model would otherwise miss.

## Contents

- Correctness
- Security
- Standards
- Smell baseline
- Spec
- Weigh and disagree

## Correctness

Look past the hunk to callers and callees the diff doesn't touch: a changed return shape, a new `null`, a renamed key, a swallowed error, a lock or ordering assumption. A new behaviour with no test, or a test that can't fail (asserts the mock), is a **Test** finding.

A test whose expected value changed in the same diff as the code it tests is suspect: the change may bend the test to the new output rather than fix the code. Each one needs a reason from the intended behaviour: the spec, the issue, the PR body. An expectation that changed with no such reason is a **Test** finding; quote the old and new value.

## Security

Part of the Correctness axis. A **Security** finding names five things: the lower-trust principal, the input or action they control, the check that should stop them, the boundary crossed, and the concrete result for another principal or resource ("any logged-in user reads another tenant's notes"). Missing one, it isn't **Security**: a missing best practice, a crash that only hurts the caller, or self-impact is a **Bug** or **Smell** at most.

- **One working control is enough.** When a layer the diff keeps already stops the attack, a missing second layer is a hardening note: **Smell**, not **Security**.
- **Don't guess what the repo can't show.** When the finding depends on proxy, header, identity-provider or deployment settings that aren't in the repository, assume neither their presence nor absence: put it in the summary (Local mode: the report, as not checked, not a finding to fix) with the exact fact that would settle it, not as an inline **Security** comment.
- **Rate what the trigger demonstrates.** The **rating** goes in brackets after the label, ahead of an outside finding's source: ``**Security** (high): …``, ``**Security** (high; Semgrep `jwt-none-alg`): …``. Critical: an unauthenticated actor gets code execution, the whole data store, or arbitrary accounts. High: a control is fully defeated with real consequences, such as auth bypass, cross-tenant read or write, stored script running for other users, authenticated code execution, or an unauthenticated remote stop of a shared service. Medium: a real boundary violation with narrow reach or uncommon preconditions. Low: non-secret internals disclosed. Between high and medium, ask whether the control is defeated or only weakened; if you can't state the damage, it's lower than it feels.
- **Fix at the last trusted decision point**: name the invariant the code must enforce and the narrowest change that enforces it there, with a regression test that fails today.
- **Ground it in source and local tests only.** Never probe a deployed endpoint, a shared environment or a real account to prove a finding.

## Standards

Anything the repo documents about how code is written: `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `CODING_STANDARDS.md`, `GLOSSARY.md`, lint and formatter config. Search for them: when `CONTRIBUTING.md` or `CODING_STANDARDS.md` exists it must be on the list. Cite file and rule for every **Standards** finding, and skip anything tooling already enforces.

## Smell baseline

Applies even when the repo documents nothing. Two rules bind it: a documented repo standard overrides the baseline (suppress a smell the repo endorses), and every smell is a labelled judgement call ("possible Feature Envy"), never a hard violation. Report as **Smell**, quote the hunk.

Look for these Fowler smells: Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest. Name the smell and the refactoring it points to.

Duplicated Code reaches past the diff. When the diff adds a helper, utility, hook or module, search the repo for one that already does the job: `git grep` its verb and noun, and look in the folders where the repo keeps shared code. A match is **Smell** (Duplicated Code): quote both and name the one to keep.

## Spec

**Paraphrase first.** Write two or three sentences on what the diff does, from the code alone, before reading the spec source if you haven't yet, and without leaning on it if you have. A paraphrase you can't write is a finding too: the change doesn't hang together, or it hides behind its description.

Then hold the whole spec source against the paraphrase (the PR body and its linked issues; Local mode: the commit messages and any spec file found) and report as **Spec**, quoting the spec line or the hunk it leaves out: (a) requirements the spec source claims that the diff misses or shows only in part, (b) behaviour the diff has that nothing in the spec source accounts for (scope creep), (c) requirements that look implemented but are wrong. A one-line body like "Fixes #12" leaves the issue to account for the behaviour; that isn't a finding per hunk. A change can pass Standards and fail Spec, or the reverse; keep the axes distinct in the summary instead of netting them out.

## Weigh and disagree

For whoever posts and fixes (Steps 2 and 4), not for a review sub-agent: it returns every finding it can ground, unweighed.

**Weigh a grounded finding.** A real trigger doesn't mean this PR must handle it: bots review every push, so fixing everything never converges, each round landing on the last fix. Weigh three things together, with no threshold on any one:

- **Reach**: does a real user, in a setup the code claims to support (its docs, compatibility line, spec), get into the triggering state? That someone could construct it isn't enough.
- **Consequence**: a silent wrong result, lost data or a leaked credential matters even when rare; a loud failure that says what to do is acceptable in a rare setup.
- **Fix**: does it close a defect, or make the code handle a case it never claimed to handle (another host form, input shape or mode)? The second is a feature, outside the PR's scope.

All three say fix → post it to fix. A rare setup with a loud failure, or a fix that's a feature → defer it. A severe consequence on a narrow reach → post it and say it's the user's call. On lines the last fix round wrote: a defect in that fix gets fixed; a request to extend it is usually deferred.

**Disagree with evidence.** Rejecting a finding (your own on re-reading, or a bot's) cites something a reader can open: a file and symbol, a test, a spec line, a recorded decision. "This was intentional" isn't evidence; a reason that lives only in someone's head is a question for the user, not a disagree. Wanting the finding to be wrong isn't evidence either: you posted it and now judge it.
