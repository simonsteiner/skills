# Third-party skills

Skills written by other people that I use but don't own. Nothing here is forked, copied, or vendored — [`skills.json`](./skills.json) is a curated list of *which* upstream skills are worth having and *why*, and [`../scripts/sync-third-party.sh`](../scripts/sync-third-party.sh) installs them from their own repos via the [skills.sh](https://skills.sh) CLI.

```bash
./scripts/sync-third-party.sh          # install everything below, at latest
./scripts/sync-third-party.sh --check  # compare the manifest against what's installed
./scripts/sync-third-party.sh --list   # print the list with the reason for each
```

Re-running the sync re-fetches each skill, so **sync is also the upgrade command**. The flip side: there is no version pinning — every sync moves each skill to whatever is on its upstream default branch that day. Read the diff upstream before syncing if that matters.

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

## vercel-labs/skills

### Model-invoked

- **[find-skills](https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md)** — discover and install skills on demand.
