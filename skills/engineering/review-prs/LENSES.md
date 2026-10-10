# Review lenses

Read in Step 2. Each lens lists only what the model would otherwise miss.

## Contents

- Correctness
- Standards
- Smell baseline
- Spec

## Correctness

Look past the hunk to callers and callees the diff doesn't touch: a changed return shape, a new `null`, a renamed key, a swallowed error, a lock or ordering assumption. A new behaviour with no test, or a test that can't fail (asserts the mock), is a **Test** finding.

## Standards

Anything the repo documents about how code is written: `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `CODING_STANDARDS.md`, `GLOSSARY.md`, lint and formatter config. Search for them — when `CONTRIBUTING.md` or `CODING_STANDARDS.md` exists it must be on the list. Cite file and rule for every **Standards** finding, and skip anything tooling already enforces.

## Smell baseline

Applies even when the repo documents nothing. Two rules bind it: a documented repo standard overrides the baseline (suppress a smell the repo endorses), and every smell is a labelled judgement call — "possible Feature Envy" — never a hard violation. Report as **Smell**, quote the hunk.

Look for these Fowler smells: Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest. Name the smell and the refactoring it points to.

## Spec

Compare the diff to what was asked, quoting the spec line for each finding: (a) requirements missing or partial, (b) behaviour nobody asked for (scope creep), (c) requirements that look implemented but are wrong. Report as **Spec**. A change can pass Standards and fail Spec, or the reverse; keep the axes distinct in the summary instead of netting them out.
