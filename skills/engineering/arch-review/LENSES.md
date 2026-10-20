# Lenses

Two lenses, one vocabulary. Phrase every finding in codebase-design's terms: module, interface, implementation, depth, seam, adapter, leverage, locality. Translate on the way in — a "boundary" is a seam or an interface, a "thin wrapper" is a shallow module, a "layer" is a module, "an abstraction earning its keep" is the deletion test.

## Lens 1 — Deepening (produces candidates)

- Where does understanding one concept mean bouncing between many small modules?
- Where is a module shallow — its interface nearly as complex as its implementation?
- Where were pure functions extracted for testability while the bugs live in how they're called (no locality)?
- Where do coupled modules leak across their seam?
- What is untested, or hard to test through its current interface?
- Deletion test on every suspect: does deleting it concentrate complexity (keep it and deepen it) or just move it (it was a pass-through)?

## Lens 2 — Maintainability (feeds candidates or produces smaller findings)

Repo-wide, weighted to the hot spots — not just a diff.

- **Spaghetti growth:** special-case conditionals scattered through unrelated flows; one-off booleans, nullable modes, flags threaded through existing paths. Repeated conditionals on the same thing signal a missing model.
- **Unstated invariants:** casts, `any`/`unknown`, needless optionality, silent fallbacks papering over a contract. These are interface problems — the invariant belongs in the interface.
- **Wrong module:** feature logic in a shared module; a bespoke helper beside a canonical one doing the same job.
- **Size as a pointer:** files over the project's token budget (what its `file-tokens` job lists), or over ~1,000 lines when it has no such check, especially ones that crossed it recently (`git log --stat`). Look inside: several unrelated responsibilities is a candidate. One deep module over the budget is not a deepening; when a check enforces the budget it still needs a split, because the check blocks its next commit. Without a check, a long deep module is not a finding. That's a smaller finding (or it rides with the candidate touching the file), and it names the files the module splits into along its internal seams, with the interface left where it is. A deep module can span several files behind one interface.
- **Orchestration:** independent work serialized for no reason; related updates that can leave state half-applied.
- **Code judo:** is there a reframing that makes whole branches, modes, or modules disappear? Prefer it over tidying them.

A lens-2 issue that spans modules becomes a candidate; one that stays inside a module is a smaller finding.

## Approval bar (per PR, Step 7)

The PR isn't done while any of these hold, unless the report's Departures explain why:

- A visible path to delete complexity was left unused; complexity moved rather than shrank.
- A file crossed the project's token budget (or 1,000 lines, without one) because of this PR.
- New ad-hoc branching in an existing flow, or feature checks scattered through shared code.
- A new pass-through module, a single-adapter seam, or a cast-heavy interface.
- A near-duplicate of an existing helper, or logic placed outside the module that owns the concept.
- Old tests and shallow modules kept beside their replacement.
