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

- **Mysterious Name** — a name that doesn't say what it does or holds → rename; no honest name means murky design.
- **Duplicated Code** — the same logic shape in more than one hunk or file → extract and call from both.
- **Feature Envy** — a method using another object's data more than its own → move it onto the data.
- **Data Clumps** — the same few fields or params travelling together → bundle into one type.
- **Primitive Obsession** — a primitive standing in for a domain concept → give it a small type.
- **Repeated Switches** — the same switch or if-cascade on one type recurring → polymorphism or one shared map.
- **Shotgun Surgery** — one logical change forcing scattered edits → gather what changes together.
- **Divergent Change** — one file edited for several unrelated reasons → split by reason to change.
- **Speculative Generality** — abstraction or hooks for needs nobody has → inline until a real need shows.
- **Message Chains** — `a.b().c().d()` navigation callers shouldn't depend on → hide behind one method.
- **Middle Man** — a class or function that only delegates → cut it, call the target.
- **Refused Bequest** — a subclass ignoring most of what it inherits → composition over inheritance.

## Spec

Compare the diff to what was asked, quoting the spec line for each finding: (a) requirements missing or partial, (b) behaviour nobody asked for (scope creep), (c) requirements that look implemented but are wrong. Report as **Spec**. A change can pass Standards and fail Spec, or the reverse; keep the axes distinct in the summary instead of netting them out.
