# Skills

My personal collection of agent skills for real engineering. They're small, easy to adapt, composable, and work with any model — each one is a plain folder with a `SKILL.md`, following the open [Agent Skills](https://github.com/agentskills/agentskills) format, so any agent that speaks it can load them.

> This repository is a fork of Matt Pocock's [`skills`](https://github.com/mattpocock/skills). It keeps the structure of the original but maintains its own pared-down set of skills, and does not sync with upstream.

Only the engineering bucket is populated today; the rest of the structure is kept in place to grow into.

## Install

Use the [skills.sh](https://skills.sh) installer, then pick the skills and coding agents you want:

```bash
npx skills@latest add simonsteiner/skills
```

## Skills

Skills live in buckets under [`skills/`](./skills/) and split on one axis — who can invoke them. **User-invoked** skills run only when you type them; **model-invoked** skills can also be reached automatically when the task fits.

### Engineering

- **[address-review-findings](./skills/engineering/address-review-findings/SKILL.md)** _(model-invoked)_ — work through a PR's unresolved review threads, then reply and resolve.
- **[conventional-commit](./skills/engineering/conventional-commit/SKILL.md)** _(model-invoked)_ — generate a Conventional Commits v1.0.0 message from the current worktree state.
- **[sync-and-branch](./skills/engineering/sync-and-branch/SKILL.md)** _(model-invoked)_ — fast-forward the default branch and cut a fresh feature branch from it.

## Third-party skills

Skills by other people that I use but don't own are **curated, not forked**. [`third-party/skills.json`](./third-party/skills.json) records which upstream skills are worth having and why; a sync script installs them straight from their own repos, so nothing is copied into this one:

```bash
./scripts/sync-third-party.sh          # install (and upgrade) everything curated
./scripts/sync-third-party.sh --check  # compare the manifest against what's installed
```

The annotated list is in [`third-party/README.md`](./third-party/README.md).

## Developing

To hack on a skill with live edits, symlink this repo's skills into your local agent directories:

```bash
./scripts/link-skills.sh
```

This is the dev-mode equivalent of `npx skills add`: it links each skill into `~/.agents/skills` (and mirrors it for Claude Code under `~/.claude/skills`), so edits here take effect immediately. Use it on the machine where you develop the skills, and install with skills.sh everywhere else — pick one path per skill, not both.

Repo conventions are in [`CLAUDE.md`](./CLAUDE.md), and design decisions are recorded as ADRs in [`docs/adr/`](./docs/adr/).
