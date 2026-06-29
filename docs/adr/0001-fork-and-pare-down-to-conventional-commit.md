# This repo is a no-sync fork of `mattpocock/skills`, pared down to `conventional-commit`

## Context

This repository started as a fork of Matt Pocock's [`skills`](https://github.com/mattpocock/skills). That repo ships a large, interlocking set of engineering and productivity skills built around a single opinionated flow (grill → PRD → issues → implement → triage, plus domain-modeling and codebase-design vocabulary). Most of that machinery isn't part of how this repo's owner works, and tracking upstream would mean continually re-merging changes to skills that were going to be deleted anyway.

The goal was a small, owned repo: keep the structure and tooling that are useful, drop everything that isn't, and stop depending on upstream.

## Decision

**Treat this as a hard fork, not a tracking fork.**

- No `upstream` remote and no sync. `origin` is `simonsteiner/skills`; nothing pulls from `mattpocock/skills`.
- Rebranded the package and plugin from `mattpocock-skills` to `simonsteiner-skills` (`package.json`, `.claude-plugin/plugin.json`), and rewrote `README.md` / `CONTEXT.md` into a neutral voice. The README and this ADR acknowledge the fork origin and link back to the original.
- Started `CHANGELOG.md` fresh from the fork rather than carrying upstream's history.

**Pare the skill set down to a single skill: `conventional-commit`.**

- Added `conventional-commit` (the one skill worth keeping) under `skills/engineering/`.
- Deleted every other skill. Intermediate steps renamed `ask-matt → which-skill` and `setup-matt-pocock-skills → setup-skills`, but both were ultimately removed too: `which-skill` is a router with almost nothing left to route, and `setup-skills` configured an issue-tracker / triage / domain-doc ecosystem whose consuming skills no longer exist. `conventional-commit` is the only skill with no dependency on that ecosystem.
- Removed the upstream planning/meta artifacts that only described deleted skills: stray `.changeset/` entries, the previous ADR, and `.out-of-scope/` contents.

**Keep the structural scaffolding for future growth.**

- The bucket taxonomy (`engineering/`, `productivity/`, `misc/`, `personal/`, `in-progress/`, `deprecated/`) stays documented in `CLAUDE.md` even though only `engineering/` is populated, so buckets can be reintroduced without re-deciding the convention.
- `docs/adr/` and `.out-of-scope/` are kept as (otherwise empty) folders, each with a `README.md` documenting what belongs there and keeping the directory tracked in git.
- Kept `scripts/link-skills.sh` but rewrote it to mirror skills.sh's layout (symlink into the `~/.agents/skills` store, then a relative per-agent symlink into `~/.claude/skills`). It's the dev-mode equivalent of `npx skills add`, so live editing and a published install are interchangeable instead of double-linking the same skill.

## Consequences

- **Upgrades from upstream are now manual and intentional.** Picking up a future improvement from `mattpocock/skills` means deliberately copying it, not merging — which is the point.
- **The repo is small and self-consistent.** No skill references another skill that doesn't exist; the active docs describe only what's present.
- **Reintroducing the deleted flow is a real project, not a toggle.** The taxonomy and folder scaffolding lower the cost, but the skills themselves (and any `setup-skills`-style config they need) would have to be rebuilt or re-copied.
- **`conventional-commit` can be developed live** via `scripts/link-skills.sh` and shipped via skills.sh, without the two install paths colliding. Note that a dev-linked skill does not appear in `npx skills list -g`, because that reads skills.sh's lock file, which the dev link intentionally leaves untouched.
