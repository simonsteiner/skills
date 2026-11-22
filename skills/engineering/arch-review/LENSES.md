# Lenses

Three lenses, one vocabulary. Phrase every finding in codebase-design's terms: module, interface, implementation, depth, seam, adapter, leverage, locality. Translate on the way in: a "boundary" is a seam or an interface, a "thin wrapper" is a shallow module, a "layer" is a module, "an abstraction earning its keep" is the deletion test.

## Lens 1: Deepening (produces candidates)

Depth inside a module: how much it hides behind its interface. Links between modules are Lens 3's.

- Where does understanding one concept mean bouncing between many small modules?
- Where is a module shallow (its interface nearly as complex as its implementation)?
- Where were pure functions extracted for testability while the bugs live in how they're called (no locality)?
- What is untested, or hard to test through its current interface?
- Deletion test on every suspect: does deleting it concentrate complexity (keep it and deepen it) or just move it (it was a pass-through)?

## Lens 2: Maintainability (feeds candidates or produces smaller findings)

Repo-wide, weighted to the hot spots, not just a diff.

- **Spaghetti growth:** special-case conditionals scattered through unrelated flows; one-off booleans, nullable modes, flags threaded through existing paths. Repeated conditionals on the same thing signal a missing model.
- **Special cases are evidence.** Code that exists for one situation instead of following from how the system works (an `if` for one value, a parameter for one caller, a swallowed exception, a retry or sleep, a disabled test) is a requirement the design never accounted for. List each one with `path:line`, then look for the one fix that makes several of them unnecessary; it often looks nothing like them. That fix is a candidate and the special cases are its symptoms; don't file them one by one. How many remain after a batch is the measure of progress.
- **Comments that restate the code:** they change only when the code does (`// sort first so the binary search works`), so they're noise to every reader. A smaller finding. Comments about something outside the code (`// the proxy drops websockets, so we poll`) stay.
- **Unstated invariants:** casts, `any`/`unknown`, needless optionality, silent fallbacks papering over a contract. These are interface problems: the invariant belongs in the interface.
- **Wrong module:** feature logic in a shared module; a bespoke helper beside a canonical one doing the same job.
- **Size as a pointer:** files over the project's token budget (what its `file-tokens` job lists), or over ~1,000 lines when it has no such check, especially ones that crossed it recently (`git log --stat`). Look inside: several unrelated responsibilities is a candidate. One deep module over the budget is not a deepening; when a check enforces the budget it still needs a split, because the check blocks its next commit. Without a check, a long deep module is not a finding. That's a smaller finding (or it rides with the candidate touching the file), and it names the files the module splits into along its internal seams, with the interface left where it is. A deep module can span several files behind one interface.
- **Orchestration:** independent work serialized for no reason; related updates that can leave state half-applied.
- **Code judo:** is there a reframing that makes whole branches, modes, or modules disappear? Prefer it over tidying them.

A lens-2 issue that spans modules becomes a candidate; one that stays inside a module is a smaller finding.

## Lens 3: Coupling (produces candidates)

Links between modules; how deep each one is stays Lens 1's. One question: **should these pieces change together?** Pieces that change together belong together, pieces that don't shouldn't be tied, and every module depends only on modules that change less than it does. Evidence comes first: `scripts/co-change.py` lists the file pairs that keep landing in the same commit, and an import graph (script one for the stack, keep it out of the repo) shows what depends on what. There are three ways to get the answer wrong:

- **Hidden links**: pieces that must change together, where the code doesn't show it. Copies of logic or values with nothing tying them; a module reading a global or file another one sets; a feature split across folders by layer, so one change touches all of them (a high-share co-change pair in different modules is the tell); a call order or convention callers just have to know. The fix gives the link a home: one module owns the value, the feature's pieces move together, the convention becomes the interface.
- **Needless links**: pieces tied together that change for different reasons. Callers depending on internals (a leak across the seam); stable code importing something more volatile (dependency points the wrong way); a general function with a parameter only one caller understands (the caller's vocabulary leaked into the interface). A shallow module's interface changes with its implementation too, but that's depth, which Lens 1 covers.
- **Surplus**: pieces with no reason of their own to change: extension points, seams, and config for things that never vary (a single-adapter seam); dead code. A pass-through module is surplus too, but Lens 1's deletion test already finds it.
