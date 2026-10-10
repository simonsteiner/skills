# Skills

My personal collection of agent skills for real engineering. They're small, easy to adapt, composable, and work with any model — each one is a plain folder with a `SKILL.md`, following the open [Agent Skills](https://github.com/agentskills/agentskills) format, so any agent that speaks it can load them.

> This repository is a fork of Matt Pocock's [`skills`](https://github.com/mattpocock/skills). It keeps the structure of the original but maintains its own pared-down set of skills, and does not sync with upstream.

Only the engineering bucket is populated today; the rest of the structure is kept in place to grow into.

## Install

Use the [skills.sh](https://skills.sh) installer, then pick the skills and coding agents you want:

```bash
npx skills@latest add simonsteiner/skills
```

## Skill catalog

Skills live in buckets under [`skills/`](./skills/) and split on one axis — who can invoke them. **User-invoked** skills run only when you type them; **model-invoked** skills can also be reached automatically when the task fits.

### Engineering

#### User-invoked

- **[arch-review](./skills/engineering/arch-review/SKILL.md)** — scan for deepening and maintainability candidates, save a ranked backlog to `docs/arch-review/`, then ship the batch you confirm as stacked PRs.

#### Model-invoked

- **[address-review-findings](./skills/engineering/address-review-findings/SKILL.md)** — work through the unresolved review threads on one PR or a stack, then reply and resolve.
- **[conventional-commit](./skills/engineering/conventional-commit/SKILL.md)** — write Conventional Commits v1.0.0 messages and make the commits, split into atomic ones when the work spans concerns.
- **[frontend-craft](./skills/engineering/frontend-craft/SKILL.md)** — design and build UI with a point of view instead of templated defaults: pick the surface's mode, plan and self-review a token system, build to a quality floor; also critique, audit, and polish existing UI.
- **[pr-body](./skills/engineering/pr-body/SKILL.md)** — write a PR body shaped by the kind of change: before → after for a fix, a real run for a feature, unchanged output for a refactor, a few lines for a chore.
- **[review-prs](./skills/engineering/review-prs/SKILL.md)** — review open PRs (one, several, or a stack) with no real review yet or much new code since the last one, or a local diff since a fixed point, against correctness, the repo's standards and the spec; comment inline, then fix and resolve.
- **[sync-and-branch](./skills/engineering/sync-and-branch/SKILL.md)** — cut a branch from the fresh default branch, carrying uncommitted work along, and sync a fork with its upstream.

## Third-party skills

Skills by other people that I use but don't own are **curated, not forked**. [`third-party/skills.json`](./third-party/skills.json) records which upstream skills are worth having and why; a sync script installs them straight from their own repos, so nothing is copied into this one:

```bash
./scripts/sync-third-party.py          # install (and upgrade) everything curated
./scripts/sync-third-party.py --check  # compare the manifest against what's installed
```

The annotated list is in [`third-party/README.md`](./third-party/README.md).

## Developing

To hack on a skill with live edits, symlink this repo's skills into your local agent directories:

```bash
./scripts/link-skills.py          # link every owned skill, prune links to removed or deprecated ones
./scripts/link-skills.py --check  # report owned skills that aren't linked, and dead links
```

This is the dev-mode equivalent of `npx skills add`: it links each skill into `~/.agents/skills` (and mirrors it for Claude Code under `~/.claude/skills`), so edits here take effect immediately. Use it on the machine where you develop the skills, and install with skills.sh everywhere else — pick one path per skill, not both.

On that machine, `./scripts/sync-skills.py` runs `link-skills.py` and then `sync-third-party.py` (pass `--check` to check both). Run it after pulling, or after adding, moving or removing a skill, then restart your agents — they read their skill list at startup.

`./scripts/lint-skills.py` checks every skill against Anthropic's [skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), the [Agent Skills spec and best practices](https://agentskills.io/skill-creation/best-practices), and the listing rules in `AGENTS.md`; CI runs it, with shellcheck for the scripts bundled in skills, the [rumdl](https://rumdl.dev/) Markdown linter (config in `.rumdl.toml`) and [ruff](https://docs.astral.sh/ruff/) for the Python tooling (`uvx ruff check scripts tests`, config in `ruff.toml`; needs [uv](https://docs.astral.sh/uv/)), on every PR. What counts as an owned skill — its bucket, its name, no duplicates and no clash with a curated skill — is decided once, in `scripts/tooling/skill_inventory.py`, and everything about `third-party/skills.json` in `scripts/tooling/third_party.py`; the commands at the top of `scripts/` read them. `python3 -m unittest discover -s tests -t .` runs every test: `tests/tooling/` for the `scripts/tooling/` package, and `tests/skill_scripts/` for the scripts bundled in skills, against a fake `gh` so no test touches GitHub. A skill's evals run with `./scripts/eval-skill.py` against the previous version or no skill at all ([docs/evals.md](./docs/evals.md)). `npm install` sets up [lefthook](https://github.com/evilmartians/lefthook) git hooks that run the same checks on each commit, with rumdl fixing what it can.

Repo conventions are in [`AGENTS.md`](./AGENTS.md), and design decisions are recorded as ADRs in [`docs/adr/`](./docs/adr/).
