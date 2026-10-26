# Assessing t3dotgg/tstack and kentcdodds/kcd-skills

What [t3dotgg/tstack](https://github.com/t3dotgg/tstack) (at `7de017b`, 2026-10-24) and [kentcdodds/kcd-skills](https://github.com/kentcdodds/kcd-skills) (at `3dbec3c`, 2026-10-25) offer this repo, assessed 2026-10-26. Both are MIT-licensed.

## Quick summary

- **tstack** fits. It targets Claude Code, Codex and T3 Code, which is the setup used here, and fills one real gap: nothing here waits on CI, follows a PR through review bots, or merges. `review-prs` and `address-review-findings` each make one pass and stop.
- **kcd-skills** mostly doesn't. Four of its seven skills need Kent's Kody platform and private packages. It's worth mining for ideas, not curating.

## t3dotgg/tstack

| Skill | Verdict | Why |
|---|---|---|
| `babysit-pr` | **Curate** | Fills the gap above. Waits with `watch_pull_request` in T3 Code, and elsewhere with a bundled `pr-wait` script: one line per event, a lock against a second watcher, state kept across restarts, a REST fallback when GraphQL's rate limit is used up. Pushes back on review fixes that grow the PR. |
| `modernize` | **Curate** | Rebases an old PR after deciding MODERNIZE, REWORK or CLOSE; `--force-with-lease` and `git range-diff`. Nothing here overlaps it. |
| `full-send` / `full-stop` | **Adapt into an owned skill** | The proof rules, merge gate, and when-to-ask-the-user rules are strong. But they call `file-pr` and `sol-loop`, so curating them would route around `pr-body` and `review-prs`. An owned "ship it" skill could chain `pr-body` → `review-prs` → `babysit-pr`, recorded in an ADR like 0004, 0005 and 0007. |
| `leaving-pr-comments` | **Open question** | Puts a "🤖 <model> responding on behalf of <user>" note above every agent-posted comment. It's model-invoked on any GitHub comment, so it would also change how `review-prs` and `address-review-findings` comments look. `babysit-pr` and `modernize` mention it; without it that's a harmless reference to nothing. |
| `council` / `sol-loop` | Skip for now | Reviews by models from other providers (GPT Sol, Gemini) through `delegate_task`, so they would work here. They overlap `review-prs`; a cross-model option inside it would fit better than two more review skills. |
| `takeover` | Later, maybe | Finishes someone else's PR while keeping their credit. Niche, and depends on `file-pr`. |
| `file-pr` | Skip; ideas taken | `pr-body` covers it. Its title rule, ready-not-draft rule and REST fallback were adapted into `pr-body`. |

## kentcdodds/kcd-skills

| Skill | Verdict | Why |
|---|---|---|
| `ship-pr`, `friction-log`, `use-kody`, `prefer-local-kody-execute` | Skip | Need the Kody platform, its private packages, and Kent's account. |
| `visual-recap` | Skip | Its scripts hardcode `.agents/skills/` and need a `primitives.yaml` map. `pr-body` already offers Mermaid and other views. |
| `review-and-recommend` | Skip; idea taken | Five lines. The one-way / two-way door label went into `arch-review`'s candidates. `grilling` already covers presenting options with a recommendation. |
| `autopilot` | Run, don't install | Meant as a one-off: `npx kcd-skills@latest autopilot` audits a repo against a 13-rung ladder for agents shipping safely, then opens one setup PR. Worth trying on an app repo. Its first rung overlaps `docs-refactor` and `setup-lefthook`. |

The test-expectation rule from `ship-pr` and `autopilot` went into `review-prs`' Correctness lens.

## Done

- `review-prs` (`LENSES.md`): a test expectation changed in the same diff as the code it tests needs a reason from the intended behaviour, or it's a **Test** finding.
- `pr-body`: a **Title** section (follow the repo's convention, say why the change matters), open ready rather than draft, and the REST fallback for `gh pr create` / `gh pr edit` when GraphQL is rate-limited.
- `arch-review`: every candidate carries a door (`two-way` / `one-way`) on its card and in the status table, and Step 4 warns up front which rows will stop at Step 6.

## Next

1. Curate `babysit-pr` and `modernize` from `t3dotgg/tstack` in `third-party/skills.json`, with the rest of tstack listed under `archived` with these reasons.
2. Decide on `leaving-pr-comments`.
3. Write the owned ship-it skill from `full-send` / `full-stop`, with an ADR.
