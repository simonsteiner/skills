# Lenses

## Contents

- [Lens 1 — Blind spots](#lens-1--blind-spots-produces-blind-spot-candidates)
- [Lens 2 — Waste](#lens-2--waste-produces-waste-candidates)
- [Lens 3 — Infrastructure](#lens-3--infrastructure-produces-infra-candidates)

Three lenses, one vocabulary: codebase-design's module, interface, seam, adapter, depth, locality. A "unit" is a module, a "boundary" is a seam or a system boundary, a "public API" is an interface. Each lens returns findings with evidence — `path:line`, a count, a timing, a commit — never an impression.

## Lens 1 — Blind spots (produces `blind spot` candidates)

Behaviour that can break with nothing to say so. Weight everything by churn: a blind spot in a file nobody touches is a smaller finding at most.

- **Hot and unguarded.** `test-history.py drift` rows with no own test (`-`) or a low own share: the code keeps changing and its tests don't. Before calling it unguarded, grep the tests for the module's interface names; a test reaching it through another interface counts, and then the finding is weaker.
- **Fixed once, unpinned.** `test-history.py fixes` rows: each one a behaviour that broke, was fixed, and has nothing to stop it breaking again. Read the fix's diff (`git show --stat <sha>`, then the hunk); the condition it fixed is the behaviour to pin.
- **Error and edge paths.** In the hot modules, the `raise` / `throw` / `catch` / `except` / `return err` lines, guard clauses, and boundary values (empty, zero, one, max, unicode, a timezone edge) that no test drives. Coverage shows them directly when it exists; without it, compare the guard's condition with the inputs the tests use.
- **Seams with no test at them.** Exported functions, HTTP routes, CLI commands, message handlers, and adapters of a hot module that no test calls. A port with an in-memory adapter nobody uses in tests is a seam built and never tested at.
- **Run but not checked.** Tests that execute a path and assert nothing about its result: `assert result`, `toBeDefined()`, "doesn't throw", a snapshot of output too large to read. Coverage counts these lines as covered.
- **Switched off.** Skipped, `xfail`, focused (`.only`) and retried tests from Step 1. Each skip is a blind spot someone noticed; `git blame` says how long ago.

**Group by seam.** One candidate is one seam (or one module's interface) and the behaviours to pin there, each with `path:line` and its evidence line. For each seam, one line on what a test there catches and what it misses — `tdd` needs exactly that to agree the seam.

**No seam to test at** — the behaviour is reachable only by mocking the module's own collaborators or reading its private state — is a hand-off to `/arch-review`, not a candidate.

## Lens 2 — Waste (produces `waste` candidates)

Tests that cost time or edits and guard no behaviour, or guard it twice. Weight by cost: seconds per run × runs per week, and edits per refactor.

- **prune-tests' categories.** Tests that depend on the past (assert removed code stays gone), on nothing (test the browser, the mock, or the type system), or on the implementation (expected value recomputed the way the code does, private state, internal call order); duplicates; production code that exists only for tests. Tells to grep for: `existsSync(` or "not defined" on old paths; a mock of the module under test; `_private` or `__dunder` access from tests; `toHaveBeenCalledWith` / `assert_called_with` on a module the project owns; exports named `*ForTests`, `_reset*`, `@VisibleForTesting`.
- **Moves with every refactor.** `test-history.py refactors` rows: test files that commits meant to keep behaviour had to change. Read those diffs: an import path that followed a move doesn't count; changed assertions, mocks, or setup do.
- **Mocks of internals.** Count mocks of the project's own modules (`jest.mock('./`, `vi.mock('../`, `mock.patch("<own package>.`, a generated mock of an interface with one implementation) against mocks at system boundaries (network, time, randomness, the file system, a third-party API). tdd's rule is boundaries only. They're waste only where the module has a seam to rewrite them at; with no seam, the module is a hand-off (Lens 1) and its tests stay.
- **Snapshot churn.** Snapshot files changed in many commits, especially in the same commit as unrelated source: a snapshot updated wholesale is read by nobody.
- **Setup nobody needs.** Fixtures and factories no test uses (grep each name), factory fields no assertion reads, global setup every test pays for (a migrated database per test, a container per file).
- **Same behaviour, several levels.** One behaviour asserted at unit, integration and end-to-end level. Keep the cheapest level that catches its regression; end-to-end only for what needs the whole system wired.
- **Slow.** The slowest tests from Step 1, and why: a real `sleep`, real network, a container started per test, a large fixture parsed per test.
- **Flaky.** CI reruns that then passed, retry markers. One flaky test is a smaller finding (rewrite it against controlled time, randomness, or order); several sharing a cause is an `infra` candidate.

## Lens 3 — Infrastructure (produces `infra` candidates)

How the tests run, and whether that supports the `tdd` loop: one test, red or green, in seconds, at a seam, with fakes only at system boundaries.

- **Where they run.** Compare CI jobs, git hooks, and the local command. A check that runs only in CI fails late; a suite over ~10 seconds on pre-commit belongs on pre-push (setup-lefthook's rule); the same suite twice in CI with nothing varying between runs is waste; a test folder no runner config collects is never run (compare the test files found with the runner's collected count).
- **The single-test loop.** Is there a documented command for one file or one test, and how long does it take? A watch mode? Startup that dominates the run (a compile step, a global fixture, a database) is the finding.
- **Isolation.** Order dependence (shuffle where the runner supports it: `pytest -p randomly`, `jest --randomize`, `vitest --sequence.shuffle`, `go test -shuffle=on`), shared global state, tests writing into the repo or a fixed temp path, tests needing a live service or network with no fake.
- **System boundaries.** Can time, randomness, network, the database and the file system be substituted, as tdd's mocking guide expects (injected clients, an in-memory adapter or a test database)? A boundary that can't be substituted forces every test above it to be slow or to mock internals.
- **Test data.** Fixtures checked in versus built by factories; huge fixtures; recorded responses that can't be re-recorded (any change to those is a one-way door); data shared and mutated between tests.
- **Parallelism.** Does the suite run in parallel (pytest-xdist, jest workers, `go test -p`), and does it still pass when it does?
- **Coverage as a gate.** A fixed percentage enforced in CI invites tests written to move the number. Note it; it's a candidate only when the scan finds such tests.
