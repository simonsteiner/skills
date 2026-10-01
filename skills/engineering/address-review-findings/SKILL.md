---
name: address-review-findings
description: >
  Work through the review feedback on GitHub pull requests — one PR, several, or a stack — pull the unresolved threads, fix what's real, then reply and resolve. Use when the user wants to address review comments or PR feedback, respond to a reviewer, resolve review threads or conversations, asks what's left on the PR(s), or says the review came back.
---

# Address Review Findings

Turn a PR's review threads into fixes, replies, and resolutions — one decision per thread, none of them silent.

**Run the whole loop hands-off** — read, triage, fix, commit, push, reply, resolve — and report at the end. Nothing here waits for the user. What keeps that safe is what the run refuses to do, not a checkpoint: a thread is only ever resolved when it was actually addressed, and a thread that needs a human keeps itself open by staying open.

The feedback lives on GitHub, so `gh` must be authenticated (`gh auth status`). Findings produced in this session by a review skill are a different thing: act on those directly, no PR round-trip needed.

---

## Step 0 — Which PRs

No PR named → the one for the current branch. "The open PRs", a list of numbers, or "the stack" → several. Map them first:

```bash
gh pr list --state open --author @me --json number,title,headRefName,baseRefName,isDraft
```

A PR whose base is another PR's head branch is **stacked** on it. Order the set bottom-up — base first — and run Steps 1–4 once per PR in that order, checking each out before touching its code (`gh pr checkout <n>`; the tree must be clean between PRs, which it is once Step 4 has pushed). A fix made low in the stack is still missing from every PR above it until Step 4 carries it up.

---

## Step 1 — Pull the PR and its unresolved threads

```bash
gh pr view --json number,title,url,headRefName,baseRefName,state,reviewDecision,isDraft
gh pr view --comments   # review summaries and issue comments — the prose around the threads
```

Inline threads need GraphQL; the REST comments endpoint doesn't expose whether a thread is resolved. Set the three variables the query needs first — unset ones give an empty result, not an error:

```bash
OWNER="$(gh repo view --json owner --jq .owner.login)"
REPO="$(gh repo view --json name --jq .name)"
PR="$(gh pr view --json number --jq .number)"
```

```bash
gh api graphql -f query='
query($owner:String!, $repo:String!, $number:Int!) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$number) {
      reviewThreads(first:100) {
        nodes {
          id isResolved isOutdated path line startLine
          comments(first:20) { nodes { databaseId author { login } body url originalLine diffHunk } }
        }
      }
    }
  }
}' -f owner="$OWNER" -f repo="$REPO" -F number="$PR" \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not)'
```

- `id` is the thread ID — it's what replies and resolutions attach to. Keep it with each finding.
- **`line` is null on outdated threads.** Use `originalLine` and `diffHunk` to locate what the reviewer was looking at; the code has moved since.
- Read every comment in a thread, not just the first. A reviewer often answers themselves further down.
- If nothing is unresolved, say so and move to the next PR (or stop).
- **No review at all is not a clean review.** Copilot doesn't review a PR whose base is another branch, so a stacked layer can arrive with zero threads because nobody looked. Check `gh pr view <n> --json reviews --jq '.reviews | length'`; if it's 0, say so in the report rather than counting the PR as done.

---

## Step 2 — Triage each thread against the code

Open the file at the referenced line **before** deciding. The comment is a claim about the code, not a fact.

| Verdict | Meaning | What follows |
|---------|---------|--------------|
| fix | the reviewer is right | change the code |
| already fixed | a later commit resolved it | verify it really did, then reply with the commit |
| stale | thread is outdated and the code no longer exists in that form | reply explaining what replaced it |
| needs a decision | a trade-off or a scope question that isn't yours to settle | reply with the question, leave the thread open, keep going |
| disagree | the suggestion is wrong or would break something | reply with the reasoning, leave the thread open |

Never convert "disagree" into a silent resolve. An unconvinced reviewer with a closed thread is worse than an open one.

**Write the fixes straight away** and report the verdicts alongside them in Step 5. A verdict is cheaper to overrule from the diff than from a table of intentions. A *needs a decision* thread doesn't stall the run either — put the question in the thread, leave it open, and carry on with the rest.

---

## Step 3 — Apply the fixes

- Fix **what the comment is about**, not only the line it hangs on. A comment on one duplicated block usually implicates the others.
- Group into the smallest coherent commits — one concern each, not one commit per thread and not one commit for everything.
- Run whatever the repo runs (tests, linters, type checks). A review fix that breaks the build is a worse finding than the one it closed.
- Call the Skill tool with "conventional-commit" to commit. Say what changed and why, referencing the reviewer's point — never a bare "address feedback".
- Stay inside the review's scope. A review is not a mandate to refactor what nobody commented on.

---

## Step 4 — Push, reply, resolve

These post to a PR other people are watching, and a reply can't be unsent — so write each one as if the reviewer reads it without you there to explain. Then send it; no confirmation step.

Push the commits, then per thread:

```bash
# reply in the thread
gh api graphql -f query='
mutation($threadId:ID!, $body:String!) {
  addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$threadId, body:$body}) {
    comment { url }
  }
}' -f threadId="$THREAD_ID" -f body="$BODY"

# resolve it — only if it was actually addressed
gh api graphql -f query='
mutation($threadId:ID!) {
  resolveReviewThread(input:{threadId:$threadId}) { thread { isResolved } }
}' -f threadId="$THREAD_ID"
```

A reply says what changed and where — the commit SHA or the new symbol name — not "done". Resolve only threads you fixed or proved already fixed. Threads left open are the record of what still needs the reviewer.

**In a stack, carry the fixes up** before moving to the next PR. Merge each branch into the one stacked on it, bottom-up, and push — merge, not rebase, so reviewers of the upper PRs don't lose their place:

```bash
git switch <upper-head> && git merge --no-edit <lower-head> && git push
```

A conflict here is the upper PR's code meeting the fix: resolve it on the upper branch, keeping both intents, and run the checks again.

---

## Step 5 — Report

The report is the whole of the user's involvement, so it carries what a checkpoint would have: per PR, one line per thread — reviewer, file, verdict, and the commit or the reason it's still open — then what was left unaddressed and why. Link the pushed commits so any verdict can be overruled from the diff. Name any PR that had no review at all.

**Every *needs a decision* and *disagree* thread gets spelled out in the report**, not just pointed at — the user should be able to decide without opening GitHub:

> **PR #12 · `src/export.ts:40` — needs a decision**
> The reviewer wants PDF links to expire after 24h; today they never expire.
> - **A.** Expire after 24h — matches the reviewer; breaks links already sent by email.
> - **B.** Keep permanent links — current behaviour; the thread stays open.
> - **Recommended: A**, with a one-off note to existing users. [thread](url)

A line like "one thread is waiting on your decision" with no question in it is the report failing at its one job.

Merging is not part of this skill. If the user asked to merge as well, finish the report first, then call the Skill tool with "land-prs" — it merges only what's ready and retargets each PR in a stack before deleting its base.

---

## Rules of thumb

- One thread, one decision. Never bulk-resolve.
- The reviewer's diagnosis can be wrong while the symptom is real — fix the cause you find, and say so in the reply.
- Two comments that contradict each other are a question for the thread, not a coin flip — ask it there and leave the thread open.
- An outdated thread that looks fixed often isn't; the code moved, and the bug moved with it.
- Don't rewrite history on a branch under review — reviewers lose their place. Add commits.
