---
name: review-prs
compatibility: Requires git and jq, plus an authenticated gh CLI for GitHub or the az CLI with the azure-devops extension for Azure DevOps.
description: >
  Reviews pull requests on GitHub or Azure DevOps that have no real review yet or changed a lot since the last one — one PR, several, or a stack — posts the findings as inline comments, then fixes them and resolves the threads. Bot reviews such as CodeRabbit or Copilot are input to the review, not a replacement for it. Also reviews a local diff since a fixed point (commit, branch, tag) against the repo's standards and the originating spec. Use when the user wants open PRs or a branch code-reviewed, says nothing has reviewed their PRs, asks to "review since" a ref, or wants findings commented and fixed in one pass. Does not work through a reviewer's existing comments (address-review-findings) or scan for architecture candidates (arch-review).
---

# Review PRs

Review what nobody has looked at, leave the findings where the author will see them, then fix what's real. Two modes share one review:

- **PR mode** (default) — PRs on the repo's forge: find, review, comment, fix, resolve.
- **Local mode** — a fixed point is given ("review since `main`", or another skill passes one) and no PR is involved: review `git diff <fixed-point>...HEAD`, fix directly, skip Steps 0, 1 and 3. No forge needed.

**Run hands-off** and report at the end. What keeps that safe: comments only go on lines the diff touches, only findings verified against the code are posted, and a thread resolves only when a fix landed for it.

## Step 0 — Pick the forge (PR mode)

The workflow below is the same on every forge; the commands differ. Run [scripts/forge.sh](scripts/forge.sh) from the repo under review. It reads `origin` only — never `GH_REPO` or an `upstream` remote — and prints one tab-separated line whose first word picks the forge guide:

- `github <owner>/<repo>` → read [forges/github.md](forges/github.md): `gh`, with the bundled [scripts/post-review.sh](scripts/post-review.sh), [scripts/outside-findings.sh](scripts/outside-findings.sh) and [scripts/note-fixes.sh](scripts/note-fixes.sh).
- `azure-devops <org> <project> <repo>` → read [forges/azure-devops.md](forges/azure-devops.md): `az repos` and `az devops invoke`; no bundled scripts, and not yet run against a real organization.
- `unsupported <host>` (GitLab, Bitbucket, Gitea), or an error for a missing `origin` → PR mode isn't supported: say so, offer Local mode against the PR's target branch, and stop.

Read the guide before Step 1 and take every command from it; "(forge guide)" below points at one of its sections. Do its *Setup* first. Terms below are GitHub's.

## Gotchas

- **A bot's review is not a review.** CodeRabbit, Copilot, Sonar's bot, and any other automated reviewer leave input for Step 2, never a reason to skip a PR: they don't run the repo's checks, read the spec, or follow callers outside the hunk. A review that only reports its own failure ("Copilot encountered an error…", a rate-limit notice) is input of nothing. A reply in an existing thread isn't a review either, even where the forge files it as one. Only a human's review counts as real; an empty human approval counts too (*List PRs*, forge guide).
- **The review posts under the user's account**, so it only ever comments: never approve, request changes, or vote.
- A stack layer's diff is against its **base branch**, not the default branch — otherwise every layer repeats the ones below it.
- The main checkout may be switched by another session mid-run, so never switch it: read a PR from its diff, `git show <head-oid>:<path>`, or a worktree you created (Step 2).
- Shell variables don't survive between tool calls. Write a path `mktemp` printed into every later command literally, never `$wt`: an empty `$wt` makes `cd "$wt"` a silent no-op in the main checkout.
- Delete only exact paths you created (a worktree and the `mktemp -d` folder around it, `mktemp` scratch files). Never by pattern — not `/tmp/tmp.*`, not a loop over `git worktree list` matching a prefix: parallel reviewers and other sessions keep theirs there.
- A fresh worktree has no gitignored inputs (`.env`, `node_modules`, data) and a running dev server serves the main checkout. Install or copy what a check needs, never symlink it in, or name the check as not run. Never `git stash` to compare before and after: the stash is shared by every worktree.
- Don't pipe a command whose exit status matters — `git`, `gh`, `az`, this skill's scripts — into `| tail`, `| head` or `| wc -l`: the pipe reports the last command's status, so a failure reads as success or as "0 threads". Capture first, then trim or count: `out="$(<command>)" && printf '%s\n' "$out" | wc -l`.
- When a PR under review changes this skill, the installed skill may be a link into that repo, so its text and scripts change as fixes land mid-run. Read this skill's files at the start and run its scripts from a copy, using the path it prints: `d="$(mktemp -d)" && cp -r <skill-dir>/scripts "$d" && echo "$d/scripts"`.
- A command a guard or sandbox refuses stays refused. Don't re-run it through a script file or another wrapper; split it as the error asks, or skip it and say so in the report.

---

## Step 1 — Find what needs a review (PR mode)

**PRs the user names (`#12 #15`, "the stack") are reviewed, whatever their review state** — being called on a PR is the request. A recent real review only narrows a named PR to a re-review of what changed since (Step 2); with nothing changed since, review the whole PR again. Otherwise the set depends on where the call sits in the thread:

- **First message of the thread** — the call opens the thread, and the thread hasn't created or pushed to a PR yet → all open PRs: list them and filter as below, whatever branch the thread is on and whatever PRs are linked to it. Link each PR you review to the thread (`link_pull_request`, when it takes the PR's URL), so a later call in this thread finds them as its own work.
- ***continue* after a run the cap cut short** → the PRs that run's report listed as waiting, filtered and capped like a listing, not the thread's linked PRs.
- **Partway through a thread** — anything else, including a first message that opened a PR before calling this skill → the thread's own work only, whatever its review state, without the listing and filter. In T3 Code, `list_thread_pull_requests` lists the PRs linked to the current thread and the stacks they chain into: the open ones, with any stack they chain into, are the set — one PR, a stack, or several independent PRs. Merged and closed links don't count. No open PR linked → the thread's current branch: `t3_thread_read` (`threadId` from `t3_thread_configuration`) returns `branch`; outside T3 Code, the session's own checkout. A worktree thread (`worktreePath` set) owns its branch. A thread on the main checkout (`worktreePath` null) reports the checkout's current branch, which another session may have switched — the report lines below are what catch a wrong narrowing. Then:
  - **On the default branch** → say there's nothing of this thread's to review and stop.
  - **The forge has an open PR for the branch** (*List PRs*, forge guide) → that PR alone is the set, not the rest of a stack it's in; link it to the thread so the next call finds it, and open the report with "Reviewed #<n> only: it's this thread's branch", listing the other PRs that need a review.
  - **No PR, and `git rev-list --count origin/<default>..<branch>` is above 0** → Local mode with `origin/<default>` as the fixed point, in the thread's checkout. On the main checkout, first check `git rev-parse --abbrev-ref HEAD` is still `<branch>`; if it isn't, another session switched it — say so and stop rather than review and commit to someone else's branch. Open the report with "Reviewed <branch> locally: it's this thread's branch, no PR".
  - **No PR and no commits of its own** → say there's nothing committed to review and stop.

From the listing, a PR **needs a review** when either holds:

- **No real review** — no human review (see Gotchas) and no human inline comment. Bot reviews and bot threads don't count, however many.
- **Enough changed since the last real one** — diff the reviewed commit against the head: the head of the `Range:` line in the newest review-prs summary, else the newest real review's commit (*List PRs*, forge guide). About 30+ changed lines of code (not docs, lockfiles, formatting), or a new file, counts. Typo fixes and no-op rebases don't. Commits the summary's `Fixed:` line lists don't count toward it — they answer that review — but when a re-review runs, its range still starts at the reviewed commit, so the fixes get reviewed with the rest.

The set is one PR or many. A PR whose base is another open PR's head branch is **stacked** on it: order each stack base first. Independent PRs have no order. Skip drafts unless asked. Nothing needs a review → say so and stop.

**Two caps keep a run inside the session's budget**, since each review costs checks, whole-file reads and a fix pass:

- **The listing stops at 100.** A listing that returns exactly 100 PRs probably cut some off: open the report with "100+ open PRs; only the 100 newest were considered".
- **A run reviews at most 10 PRs** found by the listing — the oldest first, as they've waited longest. Every layer of a stack counts, a stack ranks by its oldest layer, and it's never split: a stack that would take the run past 10 waits for the next run, unless it's first in line. A PR based on a branch that isn't the default and isn't in the listing may have a parent the listing cut off: look for an open PR from that branch (*List PRs*, forge guide). One found → treat the two as one stack; a draft parent defers the whole stack unless drafts were asked for. None found (a `release` or `develop` target) → the PR is independent. The rest wait for the next run, which finds them because the reviewed ones now carry a real review. PRs the user named aren't capped.

Once the set is settled, rename the thread or session **only if its title is generic** — one that names no PR and no topic, as a title generated from a bare skill call does ("Review Open Pull Requests", "Code review PRs"). A title that already says what the thread is about stays as it is, even if it isn't phrased as a review — so does one another agent gave the thread when it launched it. New title: `Review #32: gate push on checks`, `Review stack #24–#31: eval runner`. In T3 Code, read the title with `t3_thread_configuration` (gives `threadId`) then `t3_thread_read`, and rename with `t3_thread_update` and `{"action": "rename", "title": "<title>"}`. A rename that errors gets fixed from the error and retried once; still failing → name it in the report. No such tool → skip this.

## Step 2 — Review each PR

Per PR (stacks bottom-up, independent PRs one at a time), read its diff against its base, and check out its head in a worktree of its own for reading whole files and running checks (*Read a PR*, forge guide). Work in the printed path until the review is posted; *Fix and resolve* (forge guide) says when to remove it.

Local mode: pin `git diff <fixed-point>...HEAD`, confirm the ref resolves and the diff isn't empty before anything else. A generic title (Step 1) becomes `Review since <fixed-point>: <topic>`.

Read the changed files whole, run the repo's checks — tests, lint, type check, what CI runs — and read the PR's checks on the forge (*Read a PR*, forge guide; a failure the diff caused, local or in CI, is a finding in this review, not a follow-up) — then read [LENSES.md](LENSES.md) and review on three axes: **Correctness**, **Standards**, **Spec**. On a re-review, review only `<reviewed-oid>..<head>` and read the existing human threads first so you don't repeat one.

**Outside findings (PR mode).** What other tools already flagged on the PR gets fixed in the same pass, so collect it yourself, not through a sub-agent, and only **after** your own review, so it can't anchor it:

Each source's commands are in *Outside findings* (forge guide).

- **CI annotations** — linters, type checkers, CodeQL, anything CI reports inline.
- **Bot reviews** — CodeRabbit, Copilot and the like: their inline threads, and what they put only in a review body or summary comment (CodeRabbit's nitpicks and "outside diff range" comments). A bot's unresolved thread you confirm isn't posted again: name it in the summary ("Confirms CodeRabbit on `src/export.ts:40`", with your severity if it differs) and Step 4 fixes it in its own thread. One you can't ground also goes in the summary, with why, so Step 4 replies rather than fixes. A real one from a review body, or from a thread someone resolved without fixing it, on a diff line becomes your own comment: Step 4 reads only unresolved threads.
- **SonarQube / SonarCloud** — when the PR's checks or a comment show a Sonar analysis, list its open issues for this PR: the SonarQube MCP tool (`search_sonar_issues_in_projects` with the `pullRequest` key from `list_pull_requests`; the forge guide names that key), else the `sonar` CLI, else, for a public SonarCloud project, `curl -s "https://sonarcloud.io/api/issues/search?componentKeys=<key>&pullRequest=<n>&resolved=false&ps=500"` (500 a page, the most it allows; page on with `&p=2` while `paging.total` is higher). The project key is in `sonar-project.properties` or the CI config. None reachable → name Sonar as not checked in the summary.
- **Other failed checks** with a reason but no annotation (a coverage gate, a security scanner's comment).

Each one is a candidate finding like your own: verify it, keep it only if the PR introduced it, and give it the severity it deserves rather than the tool's. One on a line the diff doesn't touch goes in the summary, not fixed here. Don't change an issue's status in SonarQube or dismiss an alert — a fix that lands closes it on the next analysis, and a wrong one is the user's call to dismiss.

Don't regenerate committed artifacts or re-run data pipelines to check outputs; a claim only a re-run could verify goes in the summary as not checked.

**Called partway through a thread** (Step 1) → each PR, or in Local mode the local diff, is reviewed by a fresh sub-agent, even a single one: that thread already knows what the code was *meant* to do and reads the intent into the diff. Start it empty, never as a fork or with inherited context, and give it only the PR number and its worktree path (Local mode: the fixed point, and a worktree you create at `HEAD`, which holds the same `<fixed-point>...HEAD` diff), [LENSES.md](LENSES.md), the spec source, the checks to run, and on a re-review the range and the existing human threads — no summary of the conversation, and no bot findings — plus the sub-agent rules in the next paragraph. When verifying its findings, check only that each trigger holds in the code; never drop one because the thread knows what was intended, since code that doesn't do what was intended is the finding. A thread opened for the review reviews in its own context.

Several PRs may also be reviewed in parallel by sub-agents. Every review sub-agent, mid-thread or parallel, follows the same rules: create its worktree yourself and pass the path; tell it to return findings only, edit nothing, delete nothing — including its worktree, which you remove — and keep every scratch file in `<its worktree path>/.scratch/`, never in `/tmp` or the `mktemp` folder around the worktree, so removing the worktree removes them too. Verifying, posting and fixing stay with you. When the sub-agent tool takes a model, pick it per PR: finding the bug is the sub-agent's whole job, and verifying can drop a false finding but never recover a missed one, so default to the session's model. A mid-tier model (Sonnet) is enough for a PR that's docs, config, tests only, or under about 100 changed lines of code touching no auth, money, data migration, concurrency or public API. Never the smallest tier (Haiku) for a review. A sub-agent that comes back cancelled (a harness restart) or without a result gets relaunched once; don't move on to posting or report until every one has returned.

Spec source, first match: the PR's linked issues or work items and body → a path the user gave → a file under `docs/`, `specs/` or `.scratch/` matching the branch. None found → skip the Spec axis and say so in the summary.

**Verify before you keep a finding.** Open the code and name the input or state that triggers it. Drop what you can't ground, and style opinions the repo doesn't enforce. Zero findings is a result — say what you checked. In a stack, a finding goes on the **lowest PR that introduces it**.

## Step 3 — Comment (PR mode)

One review per PR, with a summary and inline comments: post the review (forge guide). Each comment is one finding: bold severity (**Bug**, **Security**, **Test**, **Standards**, **Spec**, **Smell**, **Nit**), the problem, the trigger, the fix. An outside finding names its source and rule after the severity: ``**Bug** (SonarQube `java:S2259`) — …``, ``**Standards** (eslint `no-unused-vars`) — …``, ``**Bug** (CodeRabbit nitpick) — …``.

The summary leads with the count by severity, then the axes (Spec matched or which source was missing), the checks run, outside findings confirmed or disputed, what wasn't checked, and the range reviewed (`Range: <base-oid>..<head-oid>`). A comment whose line falls outside the diff moves into the summary. Post one PR at a time, after the payload is final.

No findings → still post the summary, so the PR stops reading as unreviewed. Comments are public and can't be unsent; post only what you'd stand behind.

## Step 4 — Fix and resolve

**PR mode:** fix every posted finding and every bot thread you confirmed, and reply to the ones you disputed: fix and resolve (forge guide). A stack is fixed one layer at a time, bottom-up, each layer's fixes carried up before the next starts — never in parallel; independent PRs may run in parallel. Expect the verdict **fix** nearly every time; if re-reading shows a finding was wrong, reply saying so and resolve it. A bot thread you disputed gets a reply with the reason and stays open. Once a PR's fixes are pushed, record them in your review summary: a `Fixed: <sha> …` line after its `Range:` line, listing the fix commits — record fixes (forge guide). Then re-read the PR's title and body: a fix that changed what they describe → call the Skill tool with "pr-body" and update both.

**Local mode:** fix each real finding, run the repo's checks, then call the Skill tool with "conventional-commit" to commit.

## Step 5 — Report

Per PR: link, the range reviewed (`<base-oid>..<head-oid>`, or `<reviewed-oid>..<head-oid>` on a re-review), findings by severity, bot findings confirmed or disputed, what was fixed (commit), what's still open and why. Include the per-thread lines from Step 4; they are the record of what each fix answered. Then a **ready to merge** verdict per PR and per stack: open threads, conflicts, a layer still based on an unmerged branch, and CI read from the forge now (*Ready to merge*, forge guide) — never a status you didn't just read. Checks still pending → watch them in the background and report when they finish, or report them as pending; never wait with `sleep`. Before reporting, `git worktree list` shows none of the worktrees you created, and the scripts copy's folder is deleted. Name every PR skipped because its review was recent enough. When the cap left PRs unreviewed, end with them and an offer to go on: "14 more PRs need a review: #41, #44, … Say *continue* to review the next 10." A *continue* runs this skill again on those PRs, under the same cap (Step 1). Local mode: findings per axis, fixed or not, checks run.

Merging is not part of this skill. Don't rewrite history on a branch under review — fixes are new commits.
