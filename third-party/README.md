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

A source can override the top-level `agents` list — `cloudflare/skills` is curated into five agents, while the other sources are curated into Claude Code and Codex. What `--check` reports:

| | |
|---|---|
| `missing` / `conflict` | curated but not installed, or installed from a different repo than the manifest names (exit 1) |
| `uncurated` | installed from a remote source but absent from the manifest |
| `unmanaged` | sitting in the store or an agent's directory with nothing managing it — another channel's install, or an upstream deletion left behind |
| `drift` | an agent directory holds an older copy of a curated skill than the store — that agent missed an update |
| `note` | store copies older than what the agents load. The CLI installs new skills straight into the agent directory and never refreshes an old `~/.agents/skills` entry, so these are leftovers, not a failed sync |

Curated skills are installed globally (`~/.agents/skills`), the same store the skills this repo owns land in, so a curated skill's name must never collide with one under [`../skills/`](../skills/). The sync script refuses to run if it does.

To add one: find it (`npx skills find`, or `/find-skills`), try it without installing (`npx skills use <owner/repo>@<skill>`), then add an entry to `skills.json` with a real reason and list it below.

## mattpocock/skills

The repo this one forked from ([ADR 0001](../docs/adr/0001-fork-and-pare-down-to-conventional-commit.md)). Pared down to `conventional-commit` for what I own; the rest of the flow is tracked from upstream instead.

### User-invoked

- **[grill-me](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md)** — a relentless interview to sharpen a plan or design.
- **[grill-with-docs](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md)** — the same interview, writing ADRs and a glossary as it goes.
- **[improve-codebase-architecture](https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md)** — scan a codebase for deepening opportunities, report them, then grill through the one you pick.

### Model-invoked

- **[code-review](https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md)** — review changes since a fixed point, on both a standards and a spec axis.
- **[codebase-design](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md)** — shared vocabulary for designing deep modules.
- **[diagnosing-bugs](https://github.com/mattpocock/skills/blob/main/skills/engineering/diagnosing-bugs/SKILL.md)** — diagnosis loop for hard bugs and performance regressions.
- **[domain-modeling](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md)** — build and sharpen a project's domain model.
- **[grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)** — the interview engine behind the grill skills.
- **[prototype](https://github.com/mattpocock/skills/blob/main/skills/engineering/prototype/SKILL.md)** — build a throwaway prototype to answer a design question.
- **[research](https://github.com/mattpocock/skills/blob/main/skills/engineering/research/SKILL.md)** — investigate a question against primary sources and land the findings as Markdown.

## cloudflare/skills

Cloudflare's own skills for the developer platform, all retrieval-first over live Cloudflare docs. These arrived through a plugin marketplace and sat outside the manifest as frozen copies until [ADR 0003](../docs/adr/0003-move-the-cloudflare-skills-onto-the-curated-channel.md) moved them onto this channel; the repo's `commands/` and `rules/` are deliberately not curated, since only its Claude Code plugin installs those.

### Model-invoked

- **[cloudflare](https://github.com/cloudflare/skills/blob/main/skills/cloudflare/SKILL.md)** — umbrella platform skill: Workers, storage, AI, networking, security, IaC.
- **[wrangler](https://github.com/cloudflare/skills/blob/main/skills/wrangler/SKILL.md)** — correct CLI syntax for deploys and resource management.
- **[workers-best-practices](https://github.com/cloudflare/skills/blob/main/skills/workers-best-practices/SKILL.md)** — authoring and reviewing Workers against production practices.
- **[durable-objects](https://github.com/cloudflare/skills/blob/main/skills/durable-objects/SKILL.md)** — stateful coordination, RPC, SQLite storage, alarms, WebSockets.
- **[agents-sdk](https://github.com/cloudflare/skills/blob/main/skills/agents-sdk/SKILL.md)** — agents on Workers: durable execution, queues, retries, React hooks.
- **[sandbox-stable](https://github.com/cloudflare/skills/blob/main/skills/sandbox-stable/SKILL.md)** — sandboxed code execution on the stable `@cloudflare/sandbox` package.
- **[cloudflare-email-service](https://github.com/cloudflare/skills/blob/main/skills/cloudflare-email-service/SKILL.md)** — transactional email, routing, and the SPF/DKIM/DMARC setup.
- **[turnstile-spin](https://github.com/cloudflare/skills/blob/main/skills/turnstile-spin/SKILL.md)** — Turnstile end to end, including server-side siteverify.
- **[web-perf](https://github.com/cloudflare/skills/blob/main/skills/web-perf/SKILL.md)** — Core Web Vitals and load analysis via Chrome DevTools MCP.
- **[cloudflare-one](https://github.com/cloudflare/skills/blob/main/skills/cloudflare-one/SKILL.md)** — Zero Trust and SASE: Access, Gateway, WARP, Tunnel, device posture.
- **[cloudflare-one-migrations](https://github.com/cloudflare/skills/blob/main/skills/cloudflare-one-migrations/SKILL.md)** — migrations off Zscaler, Palo Alto, or a legacy VPN.

## cursor/plugins

Cursor's plugin monorepo ships 78 skills across many kits. One is curated.

### User-invoked

- **[thermo-nuclear-code-quality-review](https://github.com/cursor/plugins/blob/main/cursor-team-kit/skills/thermo-nuclear-code-quality-review/SKILL.md)** — a deliberately harsh maintainability review of a branch: abstraction quality, giant files, spaghetti conditions, and restructurings that simplify without changing behaviour. Complements `code-review` (standards and spec) rather than replacing it.

Upstream also ships `thermo-nuclear-review` (security and correctness) and `thermos`, which runs both in parallel. Neither is curated, so `thermos` would only find half its inputs.

## vercel-labs/skills

### Model-invoked

- **[find-skills](https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md)** — discover and install skills on demand.
