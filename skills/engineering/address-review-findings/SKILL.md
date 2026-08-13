---
name: address-review-findings
description: >
  Work through the review feedback on a GitHub pull request — pull the unresolved threads, fix what's real, then reply and resolve. Use when the user wants to address review comments or PR feedback, respond to a reviewer, resolve review threads, asks what's left on the PR, or says the review came back.
---

# Address Review Findings

Turn a PR's review threads into fixes, replies, and resolutions — one decision per thread, none of them silent.

The feedback lives on GitHub, so `gh` must be authenticated (`gh auth status`). Findings produced in this session by a review skill are a different thing: act on those directly, no PR round-trip needed.

---

## Step 1 — Pull the PR and its unresolved threads

```bash
gh pr view --json number,title,url,headRefName,baseRefName,state,reviewDecision,isDraft
gh pr view --comments   # review summaries and issue comments — the prose around the threads
```

Inline threads need GraphQL; the REST comments endpoint doesn't expose whether a thread is resolved.

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

`$OWNER`/`$REPO` come from `gh repo view --json owner,name`; `$PR` from step 1.

- `id` is the thread ID — it's what replies and resolutions attach to. Keep it with each finding.
- **`line` is null on outdated threads.** Use `originalLine` and `diffHunk` to locate what the reviewer was looking at; the code has moved since.
- Read every comment in a thread, not just the first. A reviewer often answers themselves further down.
- If nothing is unresolved, say so and stop.

---

## Step 2 — Triage each thread against the code

Open the file at the referenced line **before** deciding. The comment is a claim about the code, not a fact.

| Verdict | Meaning | What follows |
|---------|---------|--------------|
| fix | the reviewer is right | change the code |
| already fixed | a later commit resolved it | verify it really did, then reply with the commit |
| stale | thread is outdated and the code no longer exists in that form | reply explaining what replaced it |
| needs a decision | a trade-off or a scope question that isn't yours to settle | ask the user, leave the thread open |
| disagree | the suggestion is wrong or would break something | reply with the reasoning, leave the thread open |

Never convert "disagree" into a silent resolve. An unconvinced reviewer with a closed thread is worse than an open one.

Present the triage before touching code, so the user can overrule any verdict.

---

## Step 3 — Apply the fixes

- Fix **what the comment is about**, not only the line it hangs on. A comment on one duplicated block usually implicates the others.
- Group into the smallest coherent commits — one concern each, not one commit per thread and not one commit for everything.
- Run whatever the repo runs (tests, linters, type checks). A review fix that breaks the build is a worse finding than the one it closed.
- Write the messages with the `conventional-commit` skill. Say what changed and why, referencing the reviewer's point — never a bare "address feedback".
- Stay inside the review's scope. A review is not a mandate to refactor what nobody commented on.

---

## Step 4 — Push, reply, resolve

These post to a PR other people are watching. **Show the user the exact reply text per thread and get an explicit go-ahead first.**

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

---

## Step 5 — Report

One line per thread: reviewer, file, verdict, and the commit or the reason it's still open. Then state plainly what was left unaddressed and why. If any thread needed the user's decision, ask now.

---

## Rules of thumb

- One thread, one decision. Never bulk-resolve.
- The reviewer's diagnosis can be wrong while the symptom is real — fix the cause you find, and say so in the reply.
- Two comments that contradict each other are a question for the user, not a coin flip.
- An outdated thread that looks fixed often isn't; the code moved, and the bug moved with it.
- Don't rewrite history on a branch under review — reviewers lose their place. Add commits.
