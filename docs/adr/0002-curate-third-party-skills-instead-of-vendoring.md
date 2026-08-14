# Third-party skills are curated in a manifest, never vendored into this repo

## Context

[ADR 0001](./0001-fork-and-pare-down-to-conventional-commit.md) made this a hard fork: the repo owns one skill and doesn't track upstream. But most of the skills actually in daily use are still other people's — ten from `mattpocock/skills`, one from `vercel-labs/skills`. They were installed ad hoc with `npx skills add`, which meant the list of what's installed, and the reason each one was chosen, lived nowhere but the machine's `~/.agents/.skill-lock.json`.

The want was a curated list that's easy to install and upgrade, without forking each upstream repo.

Three ways to do that:

1. **Fork each upstream repo** — rejected outright by the brief, and ADR 0001 already documents why tracking forks are a bad trade here.
2. **Vendor the skills into `skills/`** (git subtree, sparse checkout, or plain copies). Gives pinned versions and offline access, but re-publishes other people's work under this repo's plugin name, forces `README.md` and `.claude-plugin/plugin.json` entries for skills that aren't ours, and makes every upstream fix a manual merge.
3. **Curate a manifest and let the skills.sh CLI fetch from upstream.** The CLI already installs individual skills out of a repo (`skills add <repo> -s <names>`), and re-running `add` refetches an installed skill in place — so install and upgrade are the same command.

## Decision

**Option 3. This repo publishes the skills it owns and merely references the ones it doesn't.**

- [`third-party/skills.json`](../../third-party/skills.json) is the source of truth: upstream repo, skill names, and a written reason for each pick. The reason is the point — an unexplained entry is a candidate for deletion.
- [`scripts/sync-third-party.sh`](../../scripts/sync-third-party.sh) drives the skills.sh CLI from that manifest. No args installs everything at latest; `--check` diffs the manifest against the lock file (reporting both missing and *uncurated* installs); `--list` prints the list with reasons.
- Curated skills stay out of `skills/`, the top-level `README.md` skill list, and `.claude-plugin/plugin.json`. Their annotated list lives in [`third-party/README.md`](../../third-party/README.md), grouped user-invoked / model-invoked like the buckets are.
- Owned and curated skills share one global store (`~/.agents/skills`), so names must be unique across both sets. The sync script hard-fails on a collision rather than letting whichever synced last silently win.

## Consequences

- **No version pinning.** Every sync moves each skill to whatever is on its upstream default branch that day; the CLI's `skillFolderHash` detects change but doesn't pin. An upstream rewrite lands silently on the next sync. Accepted deliberately — pinning is the one thing that would justify vendoring, and it isn't worth the cost yet.
- **Upstream deletions and renames break the sync**, loudly, at install time. That's the intended failure mode: a skill that vanished upstream should force a decision, not linger as a stale copy.
- **The manifest can drift from reality** — nothing forces a sync after an edit, and skills added by hand with `npx skills add` won't be in it. `--check` exists to surface both directions of drift; it isn't run automatically.
- **Publisher and consumer roles stay separate.** `npx skills add simonsteiner/skills` still installs exactly the skills this repo wrote, and no attribution or licensing question arises from re-shipping someone else's work.

## When to revisit

"A git repo plus scripts" is a known pattern with a known critique — [localskills.sh's roundup of skills.sh alternatives](https://localskills.sh/blog/skills-sh-alternatives) puts it as total control bought with total maintenance burden, where you end up rebuilding versioning, per-tool format translation, and access control by hand: fine at very small scale, unreasonable past a handful of engineers. (It's a registry vendor's post, so read the conclusion with that in mind.)

Half of that critique doesn't land here, because this isn't fully DIY: fetching from upstream and wiring skills into each agent's directory are the skills.sh CLI's job, and the format is the [Agent Skills](https://github.com/agentskills/agentskills) spec, so there's no per-tool translation to maintain. What this repo owns is only the curated list. The half that does land is versioning — no pinning, no rollback — and there is no access control at all, which is fine while everything curated is public and the audience is one person.

The triggers to move to a registry with real versioning (localskills.sh, or whatever the equivalent is by then) are: more than a couple of people consuming this list, needing to pin or roll back a skill version, or wanting private skills in the same flow.
