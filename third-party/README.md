# Third-party skills

Skills written by other people that I use but don't own. Nothing here is forked, copied, or vendored — [`skills.json`](./skills.json) is a curated list of *which* upstream skills are worth having and *why*, and [`../scripts/sync-third-party.sh`](../scripts/sync-third-party.sh) installs them from their own repos via the [skills.sh](https://skills.sh) CLI.

From the repo root:

```bash
./scripts/sync-third-party.sh          # install everything below, at latest
./scripts/sync-third-party.sh --check  # compare the manifest against what's installed
./scripts/sync-third-party.sh --list   # print the list with the reason for each
```

Re-running the sync re-fetches each skill, so **sync is also the upgrade command**. The flip side: there is no version pinning — every sync moves each skill to whatever is on its upstream default branch that day. Read the diff upstream before syncing if that matters.

**Run the sync from a plain terminal, not from inside a coding-agent session.** The CLI detects the agent it's running under and installs to that agent alone, so a sync started inside Claude Code updates the store and Claude Code and silently leaves every other agent on its old copy.

A source can override the top-level `agents` list — `cloudflare/skills` is curated into five agents, while the other sources are curated into Claude Code and Codex.

The skills.sh CLI treats Codex, GitHub Copilot, Gemini CLI and Antigravity as "universal" agents: a global install writes only the store, `~/.agents/skills`, and never their own directories. So the sync links each curated skill into `~/.codex/skills`, `~/.copilot/skills`, `~/.gemini/skills` and `~/.gemini/antigravity/skills` itself, for the agents its source lists. A real directory already sitting there is a stale copy from another channel; the sync refuses to replace it, and `--check` says so.

What `--check` reports:

| | |
|---|---|
| `missing` / `conflict` | curated but not installed, or installed from a different repo than the manifest names (exit 1) |
| `uncurated` | installed from a remote source but absent from the manifest |
| `unmanaged` | sitting in the store or an agent's directory with nothing managing it — another channel's install, or an upstream deletion left behind |
| `drift` | an agent missed an update: its directory holds an older copy than the store, a universal agent is missing its link, or holds a stale copy instead of a link (move it aside, then sync) |
| `archived` | a skill the manifest has retired is still installed |
| `note` | store copies older than what the agents load. The CLI installs new skills straight into the agent directory and never refreshes an old `~/.agents/skills` entry, so these are leftovers, not a failed sync |

Curated skills are installed globally (`~/.agents/skills`), the same store the skills this repo owns land in, so a curated skill's name must never collide with one under [[`skills/`](../skills/)](../skills/). The sync script refuses to run if it does.

To add one: find it (`npx skills find`), try it without installing (`npx skills use <owner/repo>@<skill>`), then add an entry to `skills.json` with a real reason and list it below.

## mattpocock/skills

The repo this one forked from ([ADR 0001](../docs/adr/0001-fork-and-pare-down-to-conventional-commit.md)). What I own lives under [`skills/`](../skills/); the rest of the flow is tracked from upstream instead.

### Model-invoked

- **[codebase-design](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md)** — shared vocabulary for designing deep modules.
- **[diagnosing-bugs](https://github.com/mattpocock/skills/blob/main/skills/engineering/diagnosing-bugs/SKILL.md)** — diagnosis loop for hard bugs and performance regressions.
- **[domain-modeling](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md)** — build and sharpen a project's domain model.
- **[grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)** — the interview engine; fires on "grill me" and friends by itself.
- **[research](https://github.com/mattpocock/skills/blob/main/skills/engineering/research/SKILL.md)** — investigate a question against primary sources and land the findings as Markdown.
- **[tdd](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md)** — test-first red → green at agreed seams, and what a test worth keeping looks like.
- **[wizard](https://github.com/mattpocock/skills/blob/main/skills/engineering/wizard/SKILL.md)** — generate a bash wizard that walks a human through steps only they can do.

## cloudflare/skills

Cloudflare's own skills for the developer platform, all retrieval-first over live Cloudflare docs. These arrived through a plugin marketplace and sat outside the manifest as frozen copies until [ADR 0003](../docs/adr/0003-move-the-cloudflare-skills-onto-the-curated-channel.md) moved them onto this channel; the repo's `commands/` and `rules/` are deliberately not curated, since only its Claude Code plugin installs those.

### Model-invoked

- **[cloudflare](https://github.com/cloudflare/skills/blob/main/skills/cloudflare/SKILL.md)** — umbrella platform skill: Workers, storage, AI, networking, security, IaC.
- **[wrangler](https://github.com/cloudflare/skills/blob/main/skills/wrangler/SKILL.md)** — correct CLI syntax for deploys and resource management.
- **[workers-best-practices](https://github.com/cloudflare/skills/blob/main/skills/workers-best-practices/SKILL.md)** — authoring and reviewing Workers against production practices.
- **[web-perf](https://github.com/cloudflare/skills/blob/main/skills/web-perf/SKILL.md)** — Core Web Vitals and load analysis via Chrome DevTools MCP.

## Archived

Curated once, then retired. Each stays in `skills.json` under its source's `archived` list with the reason, so the decision isn't re-litigated; the sync no longer installs it, and `--check` reports an `archived` line while a copy is still installed (`npx skills remove -g <name>` clears it).

- **[improve-codebase-architecture](https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md)** (mattpocock/skills) — and
- **[thermo-nuclear-code-quality-review](https://github.com/cursor/plugins/blob/main/cursor-team-kit/skills/thermo-nuclear-code-quality-review/SKILL.md)** (cursor/plugins) — both replaced by the owned [`arch-review`](../skills/engineering/arch-review/SKILL.md), which combines the first's deepening scan with the second's maintainability rubric and adds the save-and-implement loop neither had. See [ADR 0004](../docs/adr/0004-own-arch-review-instead-of-curating-two-review-skills.md).

- **[code-review](https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md)** (mattpocock/skills) — replaced by the owned [`review-prs`](../skills/engineering/review-prs/SKILL.md), which keeps its Standards and Spec axes and smell baseline, reviews a local fixed point in its local mode, and adds the GitHub loop. See [ADR 0005](../docs/adr/0005-own-review-prs-instead-of-curating-code-review.md).

- **[frontend-design](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md)** (anthropics/skills) — and
- **[impeccable](https://github.com/pbakaus/impeccable)** (pbakaus/impeccable) — never curated; both adapted into the owned [`frontend-craft`](../skills/engineering/frontend-craft/SKILL.md), which keeps the first's process and voice and the second's modes, quality floor, and review rubrics, without impeccable's engine, hooks, or project files. See [ADR 0007](../docs/adr/0007-own-frontend-craft-instead-of-curating-two-design-skills.md).

Archived in October 2026 because chat history (Claude transcripts from late August, prompt history from May, Codex sessions) never once invoked them:

- **mattpocock/skills:** `grill-me` and `grill-with-docs` — the model-invoked `grilling` fires on "grill" phrases by itself, and `domain-modeling` covers the docs half; `prototype`.
- **cloudflare/skills:** `cloudflare-one`, `cloudflare-one-migrations`, `sandbox-stable`, `agents-sdk`, `durable-objects`, `turnstile-spin`, `cloudflare-email-service`. The umbrella `cloudflare` skill still covers each product and points into its docs.
- **vercel-labs/skills:** `find-skills` — `npx skills find` does the same from a terminal.

Re-curating any of them is moving its entry back from `archived` to `skills`.
