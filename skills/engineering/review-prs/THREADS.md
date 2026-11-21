# Threads and sub-agents

Read in Step 1 when the call comes partway through a thread or the title is generic (in Local mode, in Step 2), and in Step 2 before starting a review sub-agent.

## The thread's own work

Called partway through a thread, the set is the thread's own work, whatever its review state, without the listing and filter. In T3 Code, `list_thread_pull_requests` lists the PRs linked to the current thread and the stacks they chain into: the open ones, with any stack they chain into, are the set — one PR, a stack, or several independent PRs. Merged and closed links don't count. No open PR linked → the thread's current branch: `t3_thread_read` (`threadId` from `t3_thread_configure`) returns `branch`; outside T3 Code, the session's own checkout. A worktree thread (`worktreePath` set) owns its branch. A thread on the main checkout (`worktreePath` null) reports the checkout's current branch, which another session may have switched — the report lines below are what catch a wrong narrowing. Then:

- **On the default branch** → say there's nothing of this thread's to review and stop.
- **The forge has an open PR for the branch** (*List PRs*, forge guide) → that PR alone is the set, not the rest of a stack it's in; link it to the thread so the next call finds it, and open the report with "Reviewed #<n> only: it's this thread's branch", listing the other PRs that need a review.
- **No PR, and `git rev-list --count origin/<default>..<branch>` is above 0** → Local mode with `origin/<default>` as the fixed point, in the thread's checkout. On the main checkout, first check `git rev-parse --abbrev-ref HEAD` is still `<branch>`; if it isn't, another session switched it — say so and stop rather than review and commit to someone else's branch. Open the report with "Reviewed <branch> locally: it's this thread's branch, no PR".
- **No PR and no commits of its own** → say there's nothing committed to review and stop.

## Thread title

Rename the thread or session **only if its title is generic** — one that names no PR and no topic, as a title generated from a bare skill call does ("Review Open Pull Requests", "Code review PRs"). A title that already says what the thread is about stays as it is, even if it isn't phrased as a review — so does one another agent gave the thread when it launched it. New title: `Review #32: gate push on checks`, `Review stack #24–#31: eval runner`; in Local mode, `Review since <fixed-point>: <topic>`. In T3 Code, read the title with `t3_thread_configure` (gives `threadId`) then `t3_thread_read`, and rename with `t3_thread_update` and `{"action": "rename", "title": "<title>"}`. A rename that errors gets fixed from the error and retried once; still failing → name it in the report. No such tool → skip this.

## Review sub-agents

**Mid-thread.** Start the sub-agent empty, never as a fork or with inherited context, and give it only the PR number and its worktree (**Worktree** below; in Local mode, the fixed point and a worktree at `HEAD` holding the same `<fixed-point>...HEAD` diff), LENSES.md, the spec source, the checks to run, and on a re-review the range and the existing human threads — no summary of the conversation, and no bot findings — plus the rules below.

**Every review sub-agent**, mid-thread or parallel, follows the same rules: tell it to return findings only, edit nothing, delete nothing — including its worktree — and keep every scratch file in `<its worktree path>/.scratch/`, never in `/tmp` or a parent `mktemp` folder, so removing the worktree removes them too. Verifying, posting and fixing stay with you.

**Worktree.** In T3 Code, use `delegate_task` with `isolation: "worktree"` instead of creating a shell worktree for a native sub-agent: T3 owns creating and removing that checkout as the child's workspace (native sub-agents such as Antigravity's time out waiting on permission prompts when running commands in an out-of-workspace `mktemp` path). When the PR's `<headRefOid>` isn't the parent checkout's `HEAD`, pass `<headRefOid>` so the delegate runs `git fetch --quiet origin "pull/<n>/head" && git checkout --detach <headRefOid>` inside its own worktree. Outside T3 Code — or when the harness has no managed worktree delegation — create the detached worktree yourself, pass the path, and remove it once the review is posted.

**Model.** When the sub-agent tool takes a model, pick it per PR: finding the bug is the sub-agent's whole job, and verifying can drop a false finding but never recover a missed one, so default to the session's model. A mid-tier model (in Claude Code, Sonnet) is enough for a PR that's docs, config, tests only, or under about 100 changed lines of code touching no auth, money, data migration, concurrency or public API. Never the harness's smallest, fastest tier (in Claude Code, Haiku) for a review.

**Returns.** A sub-agent that comes back cancelled (a harness restart), errored, timed out or without a result gets relaunched once; don't move on to posting or report until every one has returned. One that fails again didn't review: post nothing for that PR, and name it in the report as **not reviewed**, with the error. Never count it as a review with zero findings — a PR that reads as reviewed and clean is worse than one that reads as unreviewed.
