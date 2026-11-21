# simonsteiner-skills

## 1.17.0

### Minor Changes

- [#65](https://github.com/simonsteiner/skills/pull/65) [`446cebc`](https://github.com/simonsteiner/skills/commit/446cebc5f7a18109776f20064986fb1bda69497c) Thanks [@simonsteiner](https://github.com/simonsteiner)! - arch-review gains a third lens, coupling, adapted from caldoai's untangle-codebase. It asks whether pieces that change together live together, and sorts what it finds into hidden links, needless links and surplus. Lens 1 now covers depth only (shallow modules, the deletion test) and Lens 3 the links between modules, so a leak across a seam is raised once; a candidate can come from any lens. A bundled `scripts/co-change.py` lists the file pairs that keep landing in the same commit, and `--churn` ranks the most-changed files over six months for the hot-spot pass. Both leave out lockfiles, changelogs and `linguist-generated` paths, and take `--exclude <glob>`.

  Special cases now count as symptoms of a missing design: each candidate card lists the ones its fix removes, and the loose-ends audit checks they're gone. Comments that only restate the code become smaller findings. The Build step calls prune-tests on the tests of the internals a candidate replaces, never a whole file it only touched. `/arch-review next` goes straight to building when the batch is already confirmed. The skill warns against running it beside a test-review on the same repo.

  prune-tests from caldoai/skills is now curated: it deletes or rewrites tests that guard no behavior. untangle-codebase is archived in the manifest as adapted into arch-review.

- [#67](https://github.com/simonsteiner/skills/pull/67) [`28c4f4e`](https://github.com/simonsteiner/skills/commit/28c4f4e596d83621808af1ae97063dfea80fb323) Thanks [@simonsteiner](https://github.com/simonsteiner)! - New user-invoked `review-doc` skill. It reviews a design doc, plan or spec with fresh sub-agents that never saw the conversation behind it. A paraphrase lens always runs; a simplicity-and-reuse lens and an implementation-readiness lens run when the doc calls for them. It verifies each finding and disagrees only with evidence a reviewer could check. It edits the doc for clear fixes and asks you about anything that changes a decision. After such a decision, the next round runs every lens again. Rounds repeat with new reviewers until two in a row come back clean, and stop at five rounds or on churn. The report holds the full diff, and the skill deletes its scratch copies afterwards. The idea comes from Google's Elephant-Goldfish Model.

- [#66](https://github.com/simonsteiner/skills/pull/66) [`96937b9`](https://github.com/simonsteiner/skills/commit/96937b92bff6234fd796db9c51567fb1551beee5) Thanks [@simonsteiner](https://github.com/simonsteiner)! - New user-invoked skill `test-review`, an arch-review for a project's tests. It measures how the tests run: suite and single-file time, CI reruns, disabled tests, and coverage from the sonar-coverage skill, the SonarQube MCP tools or the project's own report (Vitals says when there is none). A bundled `scripts/test-history.py` reads the git history for hot code whose tests never move, fix commits that added no regression test, and tests that refactor commits had to change. The skill then scans three lenses: blind spots, waste and test infrastructure. A test that mocks internals counts as waste to rewrite when a seam exists, and goes to `/arch-review` when it doesn't.

  It saves a ranked report with a status table to `docs/test-review/`. Once you confirm the batch, which also agrees the seams `tdd` will need, it ships one stacked PR per candidate. Blind spots go through `tdd`, and every new test is seen failing. Waste goes through `prune-tests`, keeping only the deletions the card listed, with timings before and after. `/test-review next` goes straight to building when the batch is already confirmed.

### Patch Changes

- [#69](https://github.com/simonsteiner/skills/pull/69) [`e12c899`](https://github.com/simonsteiner/skills/commit/e12c899f52fcc2eaf3bbbfd8b4a946c56265efc1) Thanks [@simonsteiner](https://github.com/simonsteiner)! - conventional-commit, pr-body and sync-and-branch describe the asks they cover the way people phrase them: a commit or PR that is one step of a bigger request ("commit and open a PR", "commit directly to main", "push and open a PR"), and work that should land on a new branch, including one stacked on a named base. conventional-commit and pr-body also say to load them even for a commit or PR that looks too simple to need them, which is where most misses were. sync-and-branch now cuts from a base the user names and writes the default branch's name into later commands instead of a shell variable that doesn't survive between tool calls. conventional-commit uses `mktemp` for its hunk patch and states the no-hard-wrap rule once. All three gain evals.

- [#67](https://github.com/simonsteiner/skills/pull/67) [`9ddb9ef`](https://github.com/simonsteiner/skills/commit/9ddb9efc7675d6a1925bf285be40c0652f286596) Thanks [@simonsteiner](https://github.com/simonsteiner)! - address-review-findings disagrees only with evidence the reviewer can open; "this was intentional" becomes a question for the user instead. A reviewer's misreading still gets a clarity fix, and a finding is fixed as raised or disputed openly, never quietly downgraded. Adapted from Google's Elephant-Goldfish Model. `pick-repo.sh` now places each PR on its repo in a fork checkout, and `--head` exits 1 on a failed `gh` call instead of reading as "no PR".

- [#67](https://github.com/simonsteiner/skills/pull/67) [`cb7329b`](https://github.com/simonsteiner/skills/commit/cb7329bbcbc18b948345c1a64f079d8674c78023) Thanks [@simonsteiner](https://github.com/simonsteiner)! - docs-refactor checks design docs for four kinds of drift: missing behaviour, incomplete models, hardcoded shortcuts and divergent design. It links docs to the source it had to search for, and lists components no doc covers. Drift in an ADR goes in the report on its own line, with a superseding ADR proposed but not written. The cold read of `AGENTS.md` starts with a paraphrase of the project, and `docs/adr/` is linked from `AGENTS.md` only when it exists. With no sub-agent tool it falls back to a self-review. Adapted from Google's Elephant-Goldfish Model.

- [#82](https://github.com/simonsteiner/skills/pull/82) [`27d234c`](https://github.com/simonsteiner/skills/commit/27d234cc97d3ab2ceb7cb1427df280ac3f629125) Thanks [@simonsteiner](https://github.com/simonsteiner)! - On a GitHub Enterprise checkout, the review-prs scripts (`review-threads.sh`, `post-review.sh`, `outside-findings.sh`, `note-fixes.sh`) and the address-review-findings ones (`unresolved-threads.sh`, `reply-resolve.sh`) now query the checkout's own host instead of github.com. They take the host from a host-qualified `GH_REPO`, else from the checkout, and leave an explicit `GH_HOST` alone.

- [#67](https://github.com/simonsteiner/skills/pull/67) [`0fb3ed2`](https://github.com/simonsteiner/skills/commit/0fb3ed2afeddab4be8196039cff4f8786a7724f0) Thanks [@simonsteiner](https://github.com/simonsteiner)! - review-prs paraphrases what a diff does from the code alone and flags a PR body that claims more, or less, than the diff shows. It searches the repo for an existing helper before accepting a new one, and reports a review sub-agent that fails twice as not reviewed instead of clean. It disagrees with a finding, its own or a bot's, only with evidence a reader can check, and leaves that thread open for the user. A finding posted as the user's call waits for their answer. The skill is now self-contained: it carries its own rules for weighing and disagreeing, and tells resolved bot threads apart with its own `review-threads.sh`. With no sub-agent tool it reviews in the thread's context and says so. In T3 Code, review sub-agents run through `delegate_task` with `isolation: "worktree"`, which avoids the permission-prompt timeouts an out-of-workspace `mktemp` worktree hit under Antigravity. It also names the T3 tool `t3_thread_configure` correctly (1.16.0 called it `t3_thread_configuration`), and describes model tiers without assuming Claude. Adapted from Google's Elephant-Goldfish Model.

- [#71](https://github.com/simonsteiner/skills/pull/71) [`2601ab3`](https://github.com/simonsteiner/skills/commit/2601ab3d8e0e10ce8caaa04576faf913309f0f16) Thanks [@simonsteiner](https://github.com/simonsteiner)! - arch-review gives each phase sub-agent its own brief file (`phases/design.md`, `phases/build.md`, `phases/ship.md`) instead of the whole `SKILL.md`, so a Build or Ship sub-agent loads a few hundred tokens of instructions rather than several thousand. The per-PR approval bar moves from `LENSES.md` into the Ship brief, and the token-budget recipe lives once in `REPORT.md`. Three things change on purpose:

  - Ship updates the status row in a second commit after `gh pr create`, since the PR number isn't known before.
  - A Build sub-agent records a wrong Decision as a Departure in its commit body, for Ship to copy into the report, and can add `S` rows for out-of-scope findings.
  - Design can hand a candidate back `dropped`, with an ADR, which skips its Build and Ship.

- [#70](https://github.com/simonsteiner/skills/pull/70) [`34ef953`](https://github.com/simonsteiner/skills/commit/34ef95377d30d7e8c425ea48fdf4f8240d2a2ef8) Thanks [@simonsteiner](https://github.com/simonsteiner)! - Fixes from a skills audit. attach-media's video limit now matches its script, and its example runs as one command in a `mktemp -d` folder that it removes. address-review-findings' compatibility line lists jq. setup-lefthook explains the remote's `ref:` rule once. Credits for Google's Elephant-Goldfish Model were added where its rules were used.

- [#86](https://github.com/simonsteiner/skills/pull/86) [`54b2cfb`](https://github.com/simonsteiner/skills/commit/54b2cfb000dc867d2d85372fc14c61c4c26c12a0) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `scripts/lint-skills.py` parses `SKILL.md` frontmatter with `ruamel.yaml` instead of hand-rolled regexes. It reads YAML 1.2, rejects duplicate keys, and is locked in `pyproject.toml`/`uv.lock`; run outside the repo, it re-runs itself through the repo's uv project. It enforces an allowlist of spec fields plus `disable-model-invocation`, with strict scalar types, and disallows `metadata` in owned skills: credits go in `CREDITS.md`, the version in `plugin.json`. It checks that bundled Python scripts stay stdlib-only unless they declare PEP 723 dependencies, and flags vague description filler and boilerplate routing labels.

## 1.16.0

### Minor Changes

- [#84](https://github.com/simonsteiner/skills/pull/84) [`3e43fd9`](https://github.com/simonsteiner/skills/commit/3e43fd948b7b17f5cebfc5a856b711acca58754c) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `scripts/link-skills.py` and `scripts/sync-third-party.py` now link owned and curated skills into Antigravity's global `~/.gemini/config/skills/` directory instead of the legacy IDE path `~/.gemini/antigravity/skills/`, and `third-party/skills.json` adds `antigravity` to its default `agents` list.

- [#60](https://github.com/simonsteiner/skills/pull/60) [`da6a319`](https://github.com/simonsteiner/skills/commit/da6a319f318934c93d6920edfffd958048a0b795) Thanks [@simonsteiner](https://github.com/simonsteiner)! - address-review-findings and review-prs now weigh a correct finding before fixing it: how likely a real user is to reach the trigger, how bad the outcome is, and whether the fix closes a defect or adds a feature. A finding that's real but not worth fixing in this PR gets a new _deferred_ verdict: a reply with the reason, its bot thread resolved, and a line in the report's follow-ups. Fixing every bot finding never converged, because each round lands on the last fix.

### Patch Changes

- [#60](https://github.com/simonsteiner/skills/pull/60) [`f2b3c8e`](https://github.com/simonsteiner/skills/commit/f2b3c8e20daf3e2a5253b19f94df3dfc14f83e7d) Thanks [@simonsteiner](https://github.com/simonsteiner)! - address-review-findings and review-prs now push each PR once per fix round. Commits wait for the last one, and a stack layer's carried-up merge goes out in the same push as that layer's own fixes, so CodeRabbit and other bot reviewers start one review per round instead of one per push.

- [#60](https://github.com/simonsteiner/skills/pull/60) [`ccaa0c0`](https://github.com/simonsteiner/skills/commit/ccaa0c0a9369d77fce1432c17a05ad52770a7627) Thanks [@simonsteiner](https://github.com/simonsteiner)! - address-review-findings pushes a fix round through a bundled `scripts/push-once.sh` instead of an inline shell chain. Before pushing anything, the script refuses a bare repo, uncommitted changes, an unfinished merge, a start commit that isn't an ancestor of HEAD, or a commit count that's off. It names untracked files the round may have forgotten to add. A rejected push and any other push failure get different exit codes, so a failed login or hook no longer sends the agent into a merge.

- [#64](https://github.com/simonsteiner/skills/pull/64) [`8a418fd`](https://github.com/simonsteiner/skills/commit/8a418fd90d4027e54f56890c18f22976c88a7ba0) Thanks [@simonsteiner](https://github.com/simonsteiner)! - review-prs has a Security lens. A **Security** finding now names the lower-trust caller, what they control, the check that fails, the boundary it crosses and the concrete result for someone else, and carries a rating (`**Security** (high) — …`). A missing second layer behind a control that works is a **Smell**, and a finding that hinges on deployment config the repo doesn't hold goes in the summary with the fact to check. Adapted from Cloudflare's `security-audit` skill, which is now also curated for full codebase audits.

## 1.15.1

### Patch Changes

- [#59](https://github.com/simonsteiner/skills/pull/59) [`4904c7c`](https://github.com/simonsteiner/skills/commit/4904c7c56d0e9550b0e0f4d889692ce6f009e160) Thanks [@simonsteiner](https://github.com/simonsteiner)! - address-review-findings now picks the repo before anything else: in a fork checkout with an `upstream` remote a new `pick-repo.sh` lists gh's default repo and origin's (resolving SSH aliases, and keeping an enterprise token off an unknown origin host), and it looks each PR up on both and uses the repo that has it (or the `GH_REPO` its caller passed) for every `gh` call, and checks the PR's URL before fixing. review-prs passes its `GH_REPO` on when it hands the fixes over, so the fix step no longer reads the upstream repo's PRs.

- [#56](https://github.com/simonsteiner/skills/pull/56) [`3373cc6`](https://github.com/simonsteiner/skills/commit/3373cc6bafd9023ba58309362ea4e2333be90602) Thanks [@simonsteiner](https://github.com/simonsteiner)! - review-prs: a new `scripts/forge.sh` picks the forge from `origin` alone (Azure DevOps hosts first, then GitHub, then any host `gh` accepts), so a `GH_REPO` or a GitHub `upstream` remote no longer decides it. The GitHub and Azure DevOps guides now share the same sections, each forge's fix loop lives in its own guide, and the Azure DevOps guide is marked untested: it stops on an error rather than guess. The GitHub path is unchanged.

- [#56](https://github.com/simonsteiner/skills/pull/56) [`9517e14`](https://github.com/simonsteiner/skills/commit/9517e1477cb32a40f3b0e63aef64a8cfd201d255) Thanks [@simonsteiner](https://github.com/simonsteiner)! - review-prs: a shorter, plainer description that says what the skill does and when to use it. The mid-thread scoping steps, the thread-rename recipe and the review sub-agent brief move into a `THREADS.md` it reads only when they apply, and a new `scripts/sonar-issues.sh` pages through a public SonarCloud project's PR issues. The skill body drops from about 4,750 to 3,800 tokens with no change to what it does.

## 1.15.0

### Minor Changes

- [#55](https://github.com/simonsteiner/skills/pull/55) [`8f6d7e4`](https://github.com/simonsteiner/skills/commit/8f6d7e45371f445c3c79413b4df40fbfa315b8d9) Thanks [@simonsteiner](https://github.com/simonsteiner)! - review-prs treats bot reviews such as CodeRabbit and Copilot as input rather than a review: a PR that only bots have looked at still gets reviewed, and a PR you name always is. Each bot finding is verified: a confirmed one in an open thread is fixed there rather than posted twice, one found only in a review body or a resolved thread is posted as the skill's own comment, and a wrong one gets a reply and stays open. Thread replies no longer count as a review either. A run now reviews at most 10 PRs found by listing, keeping stacks whole, and offers to continue with the rest; a listing that hits its 100-PR ceiling says so. Each review summary records the range it covered and, once its findings are fixed, a `Fixed:` line with the fix commits: the next run starts from that range, and fix commits alone don't put a PR back in line, though a later re-review still covers them. The workflow is now forge-neutral, with the GitHub commands in `forges/github.md` and a new `forges/azure-devops.md` that runs the same review through the `az` CLI.

### Patch Changes

- [#55](https://github.com/simonsteiner/skills/pull/55) [`1dee56b`](https://github.com/simonsteiner/skills/commit/1dee56b10a784318ef01eef360a85ddb22e0612c) Thanks [@simonsteiner](https://github.com/simonsteiner)! - address-review-findings no longer counts a bot's review (CodeRabbit, Copilot, any account GitHub marks as a bot) or the empty review GitHub files for each thread reply as a real one: it still works through the bot's threads, but warns that only bots reviewed the PR and suggests running review-prs. Its PR listing now asks for up to 100 PRs instead of `gh`'s silent default of 30, and says so when it hits that ceiling.

## 1.14.0

### Minor Changes

- [#54](https://github.com/simonsteiner/skills/pull/54) [`8109dd3`](https://github.com/simonsteiner/skills/commit/8109dd303f6f03e2d6eaff3c6fb0ca41c3b01b8f) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `frontend-craft` gains an implementation lens, `MECHANICS.md`: the source-level checks a screenshot can't show, adapted from Vercel's Web Interface Guidelines. It covers form fields (`autocomplete`, labels, paste, error focus), focus and semantics, `transition: all` and interruptible motion, image dimensions and lazy loading, `color-scheme`, touch and viewport, and state, content and locale (URL state, undo for destructive actions, `Intl` formats). Builds read it when the surface has forms, URL state, media, a dark theme or touch gestures. Polish and the audit walk it over the source, and each group scores under an existing audit dimension.

### Patch Changes

- [#54](https://github.com/simonsteiner/skills/pull/54) [`a301a12`](https://github.com/simonsteiner/skills/commit/a301a12fcecba9757c0597c3dac9e7916c87fe0d) Thanks [@simonsteiner](https://github.com/simonsteiner)! - Curate `handoff` from `mattpocock/skills`, and add `vercel-labs/agent-skills` as a source for `writing-guidelines`. It's a different repo from the `vercel-labs/skills` already listed. Both skills were already installed but missing from the manifest; curating them puts them back on the upgrade path.

  Six more skills were installed the same way and are now recorded under `archived` with their reasons: `triage`, `teach`, and the `writing-fragments` / `writing-shape` / `writing-beats` drafts from `mattpocock/skills`, plus `web-design-guidelines`, which competes with `frontend-craft`'s audit mode.

## 1.13.0

### Minor Changes

- [#53](https://github.com/simonsteiner/skills/pull/53) [`df2f3c4`](https://github.com/simonsteiner/skills/commit/df2f3c4898294f26e599de62c1de6949931d7223) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `review-prs` now flags a test expectation changed alongside the code it tests when nothing explains the change. `pr-body` gains a title rule (say why the change matters), opens PRs ready rather than draft, and falls back to the REST API when GraphQL is rate-limited. `arch-review` labels each candidate a one-way or two-way door, and says before the batch starts which rows will stop for an answer.

## 1.12.0

### Minor Changes

- [#51](https://github.com/simonsteiner/skills/pull/51) [`12067e1`](https://github.com/simonsteiner/skills/commit/12067e1d87fdc7cf9a6f63b0f8a96c54194e3837) Thanks [@simonsteiner](https://github.com/simonsteiner)! - setup-lefthook adds a SonarQube job to projects analysed by SonarQube or SonarCloud. It runs the SonarQube CLI's own pre-commit check on the staged files, which scans for hardcoded secrets and for new dependency risks when a manifest changes. The job is skipped on a machine without the `sonar` CLI or not logged in, and an existing `sonar integrate git` hook is replaced by it, so lefthook stays the only hook manager.

## 1.11.0

### Minor Changes

- [#50](https://github.com/simonsteiner/skills/pull/50) [`5439e5f`](https://github.com/simonsteiner/skills/commit/5439e5fb5794f64194e28f860917f6fc3eebfde7) Thanks [@simonsteiner](https://github.com/simonsteiner)! - review-prs now fixes what other tools already flagged on a PR, along with its own findings: the annotations its check runs carry (linters, type checkers, CodeQL), collected by a new `outside-findings.sh` script, and its open SonarQube issues. Each one is verified first, and only ones the PR introduced are posted and fixed. Review sub-agents now get a model chosen per PR: the session's model by default, a mid-tier model for small, low-risk PRs, and never the smallest tier.

## 1.10.2

### Patch Changes

- [#49](https://github.com/simonsteiner/skills/pull/49) [`4a7cfa5`](https://github.com/simonsteiner/skills/commit/4a7cfa5015f41faf2aec539e906c14a0db36dacf) Thanks [@simonsteiner](https://github.com/simonsteiner)! - review-prs: called as a thread's first message, it now reviews every open PR that needs a review, even when the thread sits on a PR's branch, and links them to the thread. Called partway through a thread, it narrows to that thread's linked PRs or its current branch; a branch with no PR now gets a local review against the default branch, and a thread on the default branch stops instead of reviewing every open PR.

## 1.10.1

### Patch Changes

- [#48](https://github.com/simonsteiner/skills/pull/48) [`4bbf507`](https://github.com/simonsteiner/skills/commit/4bbf507bed53a882857d3aeb5d231439c75b04de) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `setup-lefthook` now has projects that load the token-budget remote add `".git/**"` to `exclude` in `.rumdl.toml`. lefthook clones the remote into `.git/info/lefthook-remotes/`, and rumdl walks `.git`, so `rumdl check .` linted the remote's Markdown and failed CI. The migration steps also add the remote's words to the cspell dictionary.

## 1.10.0

### Minor Changes

- [#47](https://github.com/simonsteiner/skills/pull/47) [`5fba713`](https://github.com/simonsteiner/skills/commit/5fba7136876cfcc50e02f28d391c6428c23edd71) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `setup-lefthook` no longer copies `check-file-tokens.py` into each project. A project's `lefthook.yml` now loads it from this repo as a lefthook `remotes:` entry pinned to a `filetokens.v*` tag, and keeps the `file-tokens` job (with its `--max-tokens`) in its own file, so the check fails closed when the remote can't be fetched. The skill explains how to migrate a repo that still has a copy, and the over-budget sweep runs `lefthook run pre-commit --job file-tokens --all-files`. `arch-review` finds the budget from that job and runs the check through lefthook, falling back to an old copy for repos not yet migrated.

## 1.9.0

### Minor Changes

- [#45](https://github.com/simonsteiner/skills/pull/45) [`3f04ebf`](https://github.com/simonsteiner/skills/commit/3f04ebf4450d27a6aa302c2cdf09a7c1106b8da9) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `arch-review` now works with the per-file token budget from `setup-lefthook`. It runs the project's `check-file-tokens.py` as its size lens, and gives every file over the budget a row that plans the split along the module's seams. New reports are a folder, an overview `README.md` plus one file per candidate card, so no report file goes over the budget. Older single-file reports are left as they are, and any over the budget are marked `linguist-generated`.

## 1.8.0

### Minor Changes

- [#44](https://github.com/simonsteiner/skills/pull/44) [`f951dcc`](https://github.com/simonsteiner/skills/commit/f951dcc57f0396ecab792c57c70dbb1f0706ecc6) Thanks [@simonsteiner](https://github.com/simonsteiner)! - Add `setup-lefthook`: sets up lefthook git hooks for a project's stack, following the conventions shared by my existing `lefthook.yml` files, and adds a pre-commit check that blocks any staged agent-written file over 5,000 tokens (bytes / 4), skipping lockfiles and generated code, with step-by-step instructions for splitting the file.

## 1.7.0

### Minor Changes

- [#42](https://github.com/simonsteiner/skills/pull/42) [`e9cbd48`](https://github.com/simonsteiner/skills/commit/e9cbd4861be4fc4adf094a5a95c226db2d1ab7fa) Thanks [@simonsteiner](https://github.com/simonsteiner)! - review-prs, called in a thread that already has a linked PR or stack, reviews only that instead of every open PR that needs a review; with nothing linked, an open PR on the thread's own branch counts, and the report says the review was narrowed. Called partway through a thread, it hands the review to a fresh sub-agent, even for a single PR, so the thread's knowledge of what the code was meant to do doesn't bias it. It now renames the thread only when the title is generic, keeping one that already says what the thread is about.

  It also reads CI before posting so a red job lands in the same review, sets `GH_REPO` in fork checkouts, waits for pending checks with `gh pr checks --watch` instead of `sleep`, relaunches sub-agents a harness restart cancelled, updates the PR's title and body when fixes change what they describe, and states the commit range each review covered.

### Patch Changes

- [#43](https://github.com/simonsteiner/skills/pull/43) [`3456a0e`](https://github.com/simonsteiner/skills/commit/3456a0e4c666365c2aaf805fb2ed2f09c2be45c9) Thanks [@simonsteiner](https://github.com/simonsteiner)! - review-prs: `post-review.sh` now works on PRs too big for `gh pr diff` (over 300 files or 20,000 lines), which GitHub refused with HTTP 406. It reads the hunks from GitHub's PR files API instead. A comment on a file GitHub shows no diff for, such as a large generated file, is now reported as outside the diff before posting. Before, GitHub rejected the whole review with 422 "Line could not be resolved".

## 1.6.4

### Patch Changes

- [#41](https://github.com/simonsteiner/skills/pull/41) [`227ea26`](https://github.com/simonsteiner/skills/commit/227ea265df956e641bbcdba10649638c97470247) Thanks [@simonsteiner](https://github.com/simonsteiner)! - review-prs: `post-review.sh` no longer fails with "Argument list too long" on a PR with a very large diff. address-review-findings: `unresolved-threads.sh` now honours `GH_REPO`, so it reads a fork's own PR instead of the upstream's.

## 1.6.3

### Patch Changes

- [#40](https://github.com/simonsteiner/skills/pull/40) [`3ae34b8`](https://github.com/simonsteiner/skills/commit/3ae34b84bb39a6b9974f92b002b6e2f936dcb3c0) Thanks [@simonsteiner](https://github.com/simonsteiner)! - CI workflows are hardened: actions are pinned by commit SHA (kept current by Dependabot), the lint workflow declares a read-only token and doesn't keep git credentials, and the changelog job, which can push to `main`, installs dependencies without running their install scripts.

## 1.6.2

### Patch Changes

- [#39](https://github.com/simonsteiner/skills/pull/39) [`cfec159`](https://github.com/simonsteiner/skills/commit/cfec159501efd7981f8f9b651342c9b404d103b8) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `pr-body` now reads the diff before writing and asks about files nobody discussed, asks for the why instead of inferring one, keeps internal URLs, names, and customer data out of PRs on public repos, and checks that every `#N` is an intended link.

## 1.6.1

### Patch Changes

- [#38](https://github.com/simonsteiner/skills/pull/38) [`d9de812`](https://github.com/simonsteiner/skills/commit/d9de81244a52a9f63bacfe19e882094ea46ba5e0) Thanks [@simonsteiner](https://github.com/simonsteiner)! - The third-party sync now installs Intercom's `secure-github-actions`, which hardens GitHub Actions workflow YAML against expression injection and supply-chain attacks. Intercom's other skills are recorded as declined, with reasons, in `third-party/skills.json`.

## 1.6.0

### Minor Changes

- [#37](https://github.com/simonsteiner/skills/pull/37) [`c04db96`](https://github.com/simonsteiner/skills/commit/c04db96ebb204e0bcffd6fad6ae27368605bd5f5) Thanks [@simonsteiner](https://github.com/simonsteiner)! - New model-invoked `download-media` skill: downloads the screenshots, recordings, and files attached to issues, PRs, and review comments — private repos included, where the URLs 404 without auth — so the agent can look at them, pulling frames out of recordings with ffmpeg. `address-review-findings` and `review-prs` now call it when a thread or PR body carries media.

## 1.5.0

### Minor Changes

- [#36](https://github.com/simonsteiner/skills/pull/36) [`d4edc8d`](https://github.com/simonsteiner/skills/commit/d4edc8dd810a4057775d43e45327b87d13f9672b) Thanks [@simonsteiner](https://github.com/simonsteiner)! - New model-invoked `attach-media` skill: embeds local screenshots, GIFs, and screen recordings in a PR, issue, or comment with no external hosting. It uses gh's own `--attach` (gh 2.99+) and covers what that can't reach — older gh, PRs from a fork, review comments, `gh api` bodies — with a bundled upload script. `pr-body` now calls it to embed screenshots as evidence.

## 1.4.0

### Minor Changes

- [#35](https://github.com/simonsteiner/skills/pull/35) [`1532d23`](https://github.com/simonsteiner/skills/commit/1532d23018d9609c3eb0507c25492b43ed2f4e0c) Thanks [@simonsteiner](https://github.com/simonsteiner)! - New user-invoked `docs-refactor` skill: gives each kind of doc exactly one home, fixes doc claims the code contradicts, builds a glossary with domain-modeling when there is none, and rewrites the agent instructions into a short `AGENTS.md`. It stages the result on a new branch with a report and a drafted PR body.

## 1.3.3

### Patch Changes

- [`2056966`](https://github.com/simonsteiner/skills/commit/205696684009892406cad2e2877eb7f476d4f19b) Thanks [@simonsteiner](https://github.com/simonsteiner)! - review-prs spells out the exact T3 Code rename call (`action` and `title`), retries it once from the error, and reports a rename that still fails instead of skipping it silently.

## 1.3.2

### Patch Changes

- [#34](https://github.com/simonsteiner/skills/pull/34) [`c614933`](https://github.com/simonsteiner/skills/commit/c61493331a453d426acad313415ab5003d581949) Thanks [@simonsteiner](https://github.com/simonsteiner)! - review-prs renames the current thread after the PRs it reviews (e.g. `Review [#32](https://github.com/simonsteiner/skills/issues/32): gate push on checks`) when the harness offers a rename tool, such as T3 Code's `t3_thread_update`, so review threads no longer all share a generic title. New `docs/review-prs.md` explains why a review belongs in a new thread rather than the one that wrote the PR.

## 1.3.1

### Patch Changes

- [#24](https://github.com/simonsteiner/skills/pull/24) [`24bc292`](https://github.com/simonsteiner/skills/commit/24bc292f22afff19ceb3b65af03d72815129f36e) Thanks [@simonsteiner](https://github.com/simonsteiner)! - The scripts bundled in `review-prs` and `address-review-findings` now answer `--help` (and `-h`) with their usage, without calling GitHub.

- [#24](https://github.com/simonsteiner/skills/pull/24) [`25b3bee`](https://github.com/simonsteiner/skills/commit/25b3beede266c1013b28cc47fc0a6497e317473b) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `review-prs` and `address-review-findings` no longer switch the main checkout between PRs. `review-prs` reads each PR from a detached worktree it creates and removes (fetched from `pull/<n>/head`, so PRs from forks work too), and creates the worktrees for parallel reviewers. `address-review-findings` fixes a PR in place when the checkout is already on its branch, otherwise in a detached worktree pushed with `git push origin HEAD:<branch>`, which works even when another session has the branch checked out; stack fixes are carried up by merging the pushed lower layer. Both now warn against `git stash` (shared by every worktree), pattern-based deletes, symlinking gitignored inputs into a worktree, and piping `git`/`gh` into `| tail`. Worktree paths are written out literally rather than kept in a shell variable, which doesn't survive between an agent's tool calls.

- [#24](https://github.com/simonsteiner/skills/pull/24) [`963f283`](https://github.com/simonsteiner/skills/commit/963f2839ab6c782c6c92c8c2dc4757baa37eeb2c) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `review-prs` and `address-review-findings` add the lessons of a real run on an 8-PR stack. After the first commit in a worktree they check that only that commit landed and the repo isn't bare, since a hook's tests can inherit `GIT_DIR`. They never skip hooks or rewrite pushed history unasked, and they resolve merge conflicts by editing, never with `git checkout <rev> --`. Sub-agents keep scratch files in their worktree. When a PR under review changes either skill, each runs its bundled scripts from a copy. The report reads CI from `gh pr checks` at report time, includes the per-thread lines, and confirms no worktree was left behind.

- [#24](https://github.com/simonsteiner/skills/pull/24) [`89a1e6d`](https://github.com/simonsteiner/skills/commit/89a1e6dfbd2e2193869fd53c426d1d4f392dbcfa) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `review-prs` and `address-review-findings` now give their bundled scripts' full `<skill-dir>/scripts/…` path in every command, so a copied command no longer resolves inside the repo under review, and declare what they need (`git`, `gh`, plus `jq` for `review-prs`) in a `compatibility` field. `frontend-craft`'s CSS specificity tip no longer calls class selectors "type" and "element" selectors.

- [#24](https://github.com/simonsteiner/skills/pull/24) [`57d4eaf`](https://github.com/simonsteiner/skills/commit/57d4eaf1407ac70235f8c8a801c8564ac38c25ea) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `sync-and-branch` finds the default branch with a bundled `scripts/default-branch.sh` instead of an inline shell sequence. It asks the remote only when the local `origin/HEAD` is missing or names a branch the remote no longer has, which also fixes a renamed default branch being reported under its old name. Syncing a fork always asks upstream (`--refresh`), so an upstream that switched its default branch is followed even when the old branch still exists.

## 1.3.0

### Minor Changes

- [#18](https://github.com/simonsteiner/skills/pull/18) [`0a978f8`](https://github.com/simonsteiner/skills/commit/0a978f88caed16177e30cd967d1ef94da79fae07) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `scripts/link-skills.sh` and `scripts/sync-skills.sh` are now `scripts/link-skills.py` and `scripts/sync-skills.py`, with the same flags and the same links. The repo's own tooling is now all Python.

- [#18](https://github.com/simonsteiner/skills/pull/18) [`e23cb5c`](https://github.com/simonsteiner/skills/commit/e23cb5c8e4add5ef6cd3f7bc881c8cbd44fccc5c) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `scripts/sync-third-party.sh` is now `scripts/sync-third-party.py`, with the same `--check` and `--list` modes. A source that fails to install no longer stops the sync: the other sources still install, the universal-agent links are still made, and the failures are listed at the end. `--check` now also exits 1 when a retired skill is still installed or an agent's copy is out of date, not just when a curated skill is missing or comes from the wrong repo; uncurated and unmanaged installs are still only reported. The Python tooling is linted with ruff (`uvx ruff check scripts`), which needs [uv](https://docs.astral.sh/uv/).

### Patch Changes

- [#18](https://github.com/simonsteiner/skills/pull/18) [`15ea3a5`](https://github.com/simonsteiner/skills/commit/15ea3a5d09c7471c24503f501cc63312ce76cfa8) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `scripts/lint-skills.py` now checks every listing rule in CLAUDE.md. It fails when the top-level README, a bucket README or `.claude-plugin/plugin.json` is missing a skill or lists one too many, when an entry sits under the wrong User-invoked or Model-invoked heading, when the README links an unpublished skill anywhere, and when a source, curated or archived skill in `third-party/skills.json` gives no reason. A link inside an HTML comment no longer counts as an entry, and `disable-model-invocation: true # comment` is read as `true`.

- [#18](https://github.com/simonsteiner/skills/pull/18) [`357e7b7`](https://github.com/simonsteiner/skills/commit/357e7b79652d37414448d2f3c987d3fb9936e84a) Thanks [@simonsteiner](https://github.com/simonsteiner)! - The repo's tooling now decides what an owned skill is in one place, `scripts/skill_inventory.py`. Two skills with the same name in different buckets, a skill in an unknown bucket, or an owned skill sharing a name with a curated one now fail `scripts/lint-skills.py` and stop `scripts/link-skills.sh` and `scripts/sync-third-party.sh` before they touch the skill store; a duplicate used to pass lint silently. `scripts/list-skills.sh`, which nothing called, is gone.

- [#18](https://github.com/simonsteiner/skills/pull/18) [`ac0452e`](https://github.com/simonsteiner/skills/commit/ac0452e131b420e311816faeb93f04c8038dbafe) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `review-prs` can now comment on deleted lines. Its `post-review.sh` checked every comment against new-file line numbers only, so a `"side": "LEFT"` comment on a removed line or a deleted file was rejected as outside the diff, while a LEFT comment on a line number that existed only on the new side passed and made GitHub reject the whole review. It also failed comments on files whose path holds a space or a non-ASCII character. Each end of a comment is now checked against its own side, within one hunk.

## 1.2.0

### Minor Changes

- [#16](https://github.com/simonsteiner/skills/pull/16) [`7b25c58`](https://github.com/simonsteiner/skills/commit/7b25c587d49f62f6c02c9eb85d7e159f6c324ba9) Thanks [@simonsteiner](https://github.com/simonsteiner)! - New model-invoked `frontend-craft` skill for designing and building UI with a point of view instead of templated defaults. It picks the surface's mode (Persuade, Operate, Read, Experience), plans a token system and reviews it against the brief before building, builds to a quality floor, and checks the render in bounded passes. It also critiques and audits existing UI and handles bolder, quieter, simpler, and polish requests. Adapted from Anthropic's `frontend-design` and Paul Bakaus's `impeccable`, without impeccable's engine, hooks, or project files.

This repository began as a fork of Matt Pocock's [`mattpocock-skills`](https://github.com/mattpocock/skills). It keeps the structure of the original but maintains its own pared-down set of skills and does not sync with upstream, so this changelog starts fresh from the fork rather than carrying the original's history.

## 1.1.0

### Minor Changes

- [#2](https://github.com/simonsteiner/skills/pull/2) [`45a62c7`](https://github.com/simonsteiner/skills/commit/45a62c7fdd3b5a7c0875737f084118944d191f58) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `conventional-commit` now makes the commits instead of stopping at the message. It triggers before any `git commit` — "commit", "commit and push", "commit in logical chunks", or a commit step inside another workflow — rather than only when a message is asked for, which is why it had loaded for 3 of roughly 400 agent commits and most bodies came out hard-wrapped. A mixed worktree is committed as several atomic commits staged by path, the message goes through a quoted heredoc, and the result is checked for wrapped bodies before pushing. Asking for just a message still returns one.

- [#1](https://github.com/simonsteiner/skills/pull/1) [`c833374`](https://github.com/simonsteiner/skills/commit/c833374060d983a6a257ae46a196a602d40e2a23) Thanks [@simonsteiner](https://github.com/simonsteiner)! - Add two engineering skills. `address-review-findings` pulls a PR's unresolved review threads via `gh`, triages each against the code, then fixes, pushes, replies, and resolves in one hands-off run — resolving only threads it actually addressed, and leaving anything needing a human open with the question in it. `sync-and-branch` fast-forwards the default branch and cuts a feature branch from it, branching into a new git worktree when the tree is dirty rather than stashing anything.

- [#3](https://github.com/simonsteiner/skills/pull/3) [`be8c16e`](https://github.com/simonsteiner/skills/commit/be8c16eb8b43b9315924722c3de314c4cd6c4fb9) Thanks [@simonsteiner](https://github.com/simonsteiner)! - Refresh the curated list against actual use. Curate `pr`, `tdd` and `wizard` from mattpocock/skills, and archive the skills chat history never invoked — `grill-me`, `grill-with-docs`, `prototype`, seven Cloudflare skills, and `find-skills` — each with its reason kept in `skills.json`. `arch-review` now writes PR bodies with `pr`. The repo's stale `CONTEXT.md` becomes a real `GLOSSARY.md`, following upstream's rename of that convention.

- [#10](https://github.com/simonsteiner/skills/pull/10) [`d159a63`](https://github.com/simonsteiner/skills/commit/d159a638076a87eac9ac154154ff3d71330dec01) Thanks [@simonsteiner](https://github.com/simonsteiner)! - Add `pr-body`, which replaces the curated `pr` skill (archived with its reason in `skills.json`). Across 46 PRs in six repos, `pr`'s single template forced a before/after onto features, gave one-line chores three sections, and left nowhere for stack notes, deploy steps, consumer notes or what's not done, so agents kept adding those by hand. `pr-body` keeps `pr`'s diagram views but picks the evidence by kind of change — before → after for a fix, a real run for a feature, unchanged output for a refactor, no template for a chore — folds checks into one line, and asks "what doesn't revert?" with a fixed blast-radius scale instead of one-way/two-way doors. `arch-review` now writes its PR bodies with it.

- [#9](https://github.com/simonsteiner/skills/pull/9) [`d2012c7`](https://github.com/simonsteiner/skills/commit/d2012c71f0ad5d508c66fac33d1320fdc94a297d) Thanks [@simonsteiner](https://github.com/simonsteiner)! - Cut `arch-review`'s token burn. Each candidate now runs as three fresh sub-agents — Design on the strongest model, Build and Ship on the mid-tier one — instead of one Opus implementer whose context grew to 300k+ tokens and paid for it on every review and PR turn. Scanners and every nested sub-agent (code-review's reviewers, design-it-twice's designers) also run mid-tier, every brief carries context rules (read your card not the report, ranged reads, trimmed output), smaller findings ship in PRs of at most five rows, and the skill asks for one run at a time.

- [#3](https://github.com/simonsteiner/skills/pull/3) [`d44437b`](https://github.com/simonsteiner/skills/commit/d44437b172598971a23d4c93259d96cb7b5c03d1) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `address-review-findings` handles several PRs or a stack, bottom-up, merging each fix into the PRs stacked above it. The report now spells out every thread that needs a decision — the question, the options, and a recommendation — instead of only saying one is waiting. A PR with no review at all is called out rather than counted as clean (Copilot skips PRs based on another branch), and a merge the user asks for retargets the next PR in a stack before deleting its base.

- [#11](https://github.com/simonsteiner/skills/pull/11) [`bd9dc6c`](https://github.com/simonsteiner/skills/commit/bd9dc6ceefddac71b820ad36e21d1229307a4370) Thanks [@simonsteiner](https://github.com/simonsteiner)! - Align the skills with Anthropic's skill authoring best practices. `address-review-findings` now runs bundled scripts for its GitHub calls: `unresolved-threads.sh` pages through every review thread (the inline query stopped at 100 threads and 20 comments, so a large PR could lose threads silently) and warns on a PR with no reviews, and `reply-resolve.sh` refuses an empty reply so nothing is resolved without one. `conventional-commit` drops its restatement of the spec, fixes examples that broke its own lowercase/no-period body rule, says when to read its examples file, and no longer competes with `sync-and-branch` for "commit this to a new branch". `arch-review` reads `GLOSSARY.md` only and flags a leftover `CONTEXT.md`. Descriptions are in the third person. `scripts/lint-skills.py`, run in CI with shellcheck, checks names, descriptions, body length, contents lists in long reference files, shared trigger phrases, and the README/plugin.json listing rules.

- [#3](https://github.com/simonsteiner/skills/pull/3) [`8ed4401`](https://github.com/simonsteiner/skills/commit/8ed44018c60a79b2aaf3c055caac7e6c32a6188a) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `sync-and-branch` is rewritten at a third of its length around what agents actually got wrong. It carries uncommitted work onto a branch cut from the fresh default with `git switch --no-track -c` ("commit this to a new branch"), stacks on the current branch when the changes don't apply there, and syncs a fork with its `upstream` remote — fast-forward and push when the fork carries nothing of its own, otherwise a merge on a `chore/sync-upstream-<date>` branch. The worktree route and the long preflight are gone: the harness makes worktrees, and agents cut plain branches fine without a skill. Its description now triggers only on those requests, not on every new piece of work.

- [#3](https://github.com/simonsteiner/skills/pull/3) [`326ede1`](https://github.com/simonsteiner/skills/commit/326ede18896962ee69c35ca6bdf9167ab91b7747) Thanks [@simonsteiner](https://github.com/simonsteiner)! - Add `arch-review`, a user-invoked skill that scans a codebase for deepening and maintainability candidates, saves a Markdown report to `docs/arch-review/` — styled after upstream's HTML report, with a status table, candidate cards and side-by-side before/after Mermaid diagrams — and — after you confirm the batch (every Strong candidate by default) — ships one stacked PR per candidate with its design decisions recorded and loose ends audited. It replaces the curated `improve-codebase-architecture` and `thermo-nuclear-code-quality-review`, which move to a new `archived` list in `third-party/skills.json`; the sync skips archived skills and `--check` flags any still installed. Skills now call each other with "Call the Skill tool with "name"" instead of `/skill` prose, following upstream (`docs/invocation.md`). See ADR 0004 for why arch-review is owned rather than curated.

- [#1](https://github.com/simonsteiner/skills/pull/1) [`701cfc9`](https://github.com/simonsteiner/skills/commit/701cfc988a3bca6c1b81ed67f060974f79ee8067) Thanks [@simonsteiner](https://github.com/simonsteiner)! - Curate the eleven Cloudflare skills, which had been loading from an unmanaged plugin-marketplace install frozen since July. Adds per-source agent overrides to the manifest, fixes the sync's CLI invocation (one `--skill`/`--agent` flag per value; `npx` was also draining the loop's stdin and skipping every source after the first), and teaches `--check` to report `unmanaged` and `drift` — the two failure modes that hid this.

- [#1](https://github.com/simonsteiner/skills/pull/1) [`84ca0df`](https://github.com/simonsteiner/skills/commit/84ca0dfab42362976c441209cded752d57e93746) Thanks [@simonsteiner](https://github.com/simonsteiner)! - Curate third-party skills instead of forking or vendoring them. `third-party/skills.json` lists the upstream skills worth having and why, and `scripts/sync-third-party.sh` installs and upgrades them from their own repos via the skills.sh CLI. Nothing is copied into `skills/`, so the published plugin still contains only the skills this repo owns.

### Patch Changes

- [#8](https://github.com/simonsteiner/skills/pull/8) [`e698fa0`](https://github.com/simonsteiner/skills/commit/e698fa08c165af62ae70162b539e58cf83d78d27) Thanks [@simonsteiner](https://github.com/simonsteiner)! - Link curated skills into every agent the skills.sh CLI treats as "universal" — Codex, GitHub Copilot, Gemini CLI and Antigravity — not just Codex. A global install never writes those agents' own directories, so Copilot and both Gemini agents kept loading frozen July copies of the Cloudflare skills that no sync could refresh, and `--check` told you to re-sync, which couldn't help. `--check` now verifies each link and names a stale copy as one to move aside.

- [#1](https://github.com/simonsteiner/skills/pull/1) [`c76df53`](https://github.com/simonsteiner/skills/commit/c76df53a6c93b1fa63b280a76cc56d9ec5d1cbca) Thanks [@simonsteiner](https://github.com/simonsteiner)! - Curate `thermo-nuclear-code-quality-review` from cursor/plugins, and narrow the `drift` report in `--check` to the one actionable direction — an agent directory older than the store. The reverse turned out to be normal: this CLI installs skills straight into the agent directory and never refreshes an existing `~/.agents/skills` copy, so those leftovers now get a single `note` line instead of one `drift` line each.

- [`0d43e49`](https://github.com/simonsteiner/skills/commit/0d43e497bf54279021f69687c1f4eb484b77f43c) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `scripts/link-skills.sh` now prunes links left behind by removed or deprecated skills, and `--check` reports owned skills that aren't linked. A new `scripts/sync-skills.sh` runs it and `sync-third-party.sh` in one go on the dev machine, so a new owned skill no longer stays invisible until someone remembers to re-link.

- [#13](https://github.com/simonsteiner/skills/pull/13) [`8bec03a`](https://github.com/simonsteiner/skills/commit/8bec03afcc0e0beb54ab03c57870e4c20a51c59d) Thanks [@simonsteiner](https://github.com/simonsteiner)! - `review-prs` posts through a bundled `scripts/post-review.sh`. It checks the payload and every comment's line against the diff before sending anything, and deletes the empty draft a failed post leaves behind; a hand-built `jq | gh api` pipe had left one on a PR. Reviews now run the repo's checks rather than regenerating artifacts, and don't route a refused command through a script. Files are read from a pinned ref, not a checkout another session may switch. A stack's fixes go one layer at a time.

## 1.0.0

### Initial fork

- Forked from [`mattpocock/skills`](https://github.com/mattpocock/skills) and rebranded to `simonsteiner-skills`.
- Reduced the skill set to a single skill under `skills/engineering/`:
  - **`conventional-commit`** — generate a Conventional Commits v1.0.0 message from the current worktree state.
- Removed all other skills inherited from upstream. The `productivity/`, `misc/`, `personal/`, `in-progress/`, and `deprecated/` buckets were emptied, but the taxonomy is documented in `CLAUDE.md` so they can be reintroduced later.
