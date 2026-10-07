# Own review-prs instead of curating code-review

## Context

[ADR 0004](./0004-own-arch-review-instead-of-curating-two-review-skills.md) set the bar for taking a curated skill over: the workflow needed can't be reached by calling the upstream skill, only by changing it. `code-review` (mattpocock/skills) reviews `git diff <fixed-point>...HEAD` on a Standards and a Spec axis in two parallel sub-agents and reports them side by side. It never touches GitHub.

Chat history showed the loop actually run, dozens of times, in one phrasing: "do a code review on the open PRs, if they haven't got a review yet or enough code changed since. Comment any findings and fix them." That loop is find PRs → review → post inline comments → fix → resolve → "ready to merge?". Copilot's PR review was flaky meanwhile: 9 of this repo's 10 PRs carry only a "Copilot encountered an error" stub, which any "has a review" check counts as a review. `code-review` covers one step of that loop and needs a tracker doc from a setup skill this repo doesn't use; the rest was done by hand each time.

Two review skills for one activity meant two descriptions competing for the same prompts.

## Decision

**Own `review-prs` and archive the curated `code-review`.**

- `review-prs` finds open PRs (one, several, a stack) with no real review or much new code since the last one, reviews each against its base, posts one inline-comment review per PR, then hands the threads to `address-review-findings` to fix and resolve. A review that only reports its own failure doesn't count as a review.
- It keeps what was worth keeping from upstream, MIT-credited in `CREDITS.md`: the Standards and Spec axes, the Fowler smell baseline (judgement calls that a documented repo standard overrides), and "standards files must be on the list". They live in `LENSES.md`, loaded at review time.
- A **local mode** reviews a fixed point with no PR and fixes directly — what `arch-review` needs before its PR exists. `arch-review` now calls `review-prs` instead of `code-review`.
- Dropped: mandatory parallel sub-agents (arch-review already burned a usage window), the tracker-doc setup dependency, and keeping the axes un-merged in the output.
- The skill's scripts were dropped in favour of plain `gh` commands; GraphQL thread handling stays in `address-review-findings`, where REST can't say whether a thread is resolved.

## Consequences

- **This repo maintains the adapted parts.** Upstream changes to `code-review` (the 2026-10-07 standards-search and foreground sub-agents change is already folded in) won't arrive by sync; re-read upstream occasionally.
- **`tdd` still names `code-review`** in a prose aside about the review stage. It's upstream's text, harmless, and not worth forking.
- The curated entry moves to `archived` in `skills.json`; `--check` reports a leftover install, cleared with `npx skills remove -g code-review`.
