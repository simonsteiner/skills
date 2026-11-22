# review-prs ships forge scripts and supports Azure DevOps

Supersedes the scripts bullet of [ADR 0005](./0005-own-review-prs-instead-of-curating-code-review.md) ("the skill's scripts were dropped in favour of plain `gh` commands; GraphQL thread handling stays in `address-review-findings`").

## Context

ADR 0005 dropped upstream `code-review`'s scripts and had `review-prs` call `gh` directly. In use, the inline calls were the fragile part: a `jq` failure piped into `gh api` left an empty pending review on a PR, and reading threads needs GraphQL, because REST can't say whether a thread is resolved. `AGENTS.md` has since made the rule general: fragile, exact operations go in a skill's `scripts/` folder, tested against a fake `gh`.

Azure DevOps repos came up too. The workflow is the same there, but every forge call is different.

## Decision

- `review-prs` ships bundled scripts for the exact operations: `forge.sh` (which forge `origin` points at), `post-review.sh`, `review-threads.sh` (GraphQL), `note-fixes.sh`, `outside-findings.sh` and `sonar-issues.sh`. Each is tested from `tests/skill_scripts/`.
- The workflow stays forge-neutral. The commands live in one guide per forge (`forges/github.md`, `forges/azure-devops.md`) with the same sections in the same order. `forge.sh` reads `origin` only.
- On Azure DevOps it uses the `az` CLI and fixes findings itself, since `address-review-findings` is GitHub-only.

## Consequences

- `review-prs` now owns GraphQL thread reading as well as `address-review-findings`. The two read threads for different steps; a change to one query should be checked against the other.
- The Azure DevOps guide hasn't been run against a real organization yet, so the skill stops on an `az` error instead of guessing. Other forges get Local mode only.
