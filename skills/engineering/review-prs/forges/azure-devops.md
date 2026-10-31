# Azure DevOps

**Untested:** this guide has not yet been run against a real Azure DevOps organization. When a command errors or returns something this page doesn't describe, stop and report it rather than guess a fix.

The commands review-prs runs when `forge.sh` prints `azure-devops <org> <project> <repo>`: `origin` is on `dev.azure.com`, `ssh.dev.azure.com` or `*.visualstudio.com`. No script is bundled for this forge yet: build each call from this page and check its output.

## Contents

- Setup
- List PRs
- Read a PR
- Outside findings
- Post the review
- Record fixes
- Fix and resolve
- Ready to merge

## Setup

Needs the `az` CLI with the `azure-devops` extension (`az extension show --name azure-devops`), signed in with `az login` or `AZURE_DEVOPS_EXT_PAT`. Check both before listing anything.

Take organization, project and repository from `forge.sh`'s line, already URL-decoded; its fields are tab-separated, since a project or repo name can hold spaces. Pass them on every call; never `az devops configure --defaults`, which changes the user's global config.

Terms in SKILL.md are GitHub's: here a PR's head is its source branch and newest iteration, its base the target branch.

Below, `<scope>` means `--org https://dev.azure.com/<org> --project "<project>"`, and `<thread-route>` means `--org https://dev.azure.com/<org> --area git --api-version 7.1 --route-parameters project="<project>" repositoryId="<repo>" pullRequestId=<id>`. `az devops invoke` returns `{"value": [...]}` for lists. Where it rejects `7.1`, use `7.0`.

## List PRs

```bash
az repos pr list --org https://dev.azure.com/<org> --project "<project>" --repository "<repo>" --status active --top 100 -o json
```

From it: `pullRequestId`, `title`, `createdBy.uniqueName`, `sourceRefName`, `targetRefName` (both `refs/heads/…`), `isDraft`, `reviewers[].vote`, `forkSource` (set on a PR from a fork). The open PR for one branch: add `--source-branch <branch>`. `--top 100` is the listing cap from SKILL.md Step 1.

Threads and iterations per PR:

```bash
az devops invoke <thread-route> --resource pullRequestThreads -o json
az devops invoke <thread-route> --resource pullRequestIterations -o json
```

**The head** (`<head-oid>`) is the newest iteration's `sourceRefCommit.commitId`. Not `lastMergeSourceCommit`: that is the source tip of the last merge calculation and lags a push until the merge is recalculated.

- **Real review** — any of: a non-zero `vote` from a human reviewer; an inline human thread (`threadContext` set, first comment `commentType` `text`, not `isDeleted`) by someone other than the PR's author — a general comment doesn't count; or a review-prs summary (`Range: …`). A human is an author that isn't a bot or service account (CodeRabbit posts under whatever account it was installed with — usually named for it).
- **Reviewed commit** — a review-prs summary names its range (`Range: <base>..<head>`); use that head. Otherwise take the time of the newest real review — the inline thread's `publishedDate`, or for a vote the `system` thread Azure DevOps adds when the vote is cast (`properties.CodeReviewThreadType.$value` `VoteUpdate`; property values come wrapped as `{"$type", "$value"}`) — and the iteration that was newest then: its `sourceRefCommit.commitId`. No baseline found → review the whole PR.
- **Changed since** — fetch both and diff locally: `git diff --stat <reviewed-oid> <head-oid>`. Commits the summary's `Fixed:` line lists don't count: `git log --format=%H <reviewed-oid>..<head-oid>`, then `git show --numstat <sha>` for the others.

A PR whose `targetRefName` is another open PR's `sourceRefName` is stacked on it.

## Read a PR

```bash
git fetch --prune origin
az repos pr show --org https://dev.azure.com/<org> --id <id> -o json            # description, refs, head, mergeStatus
az repos pr work-item list --org https://dev.azure.com/<org> --id <id> -o json  # linked work items: the spec
git diff origin/<target branch>...<head-oid>
tmp="$(mktemp -d)"; git worktree add --quiet --detach "$tmp/pr-<id>" <head-oid> && echo "$tmp/pr-<id>"
```

`az repos pr …` commands that take an `--id` want `--org` only, not `--project`. A PR from a fork (`forkSource` set) has its head in the fork: `git fetch "<forkSource.repository.remoteUrl>" <head-oid>`. Not the second parent of `refs/pull/<id>/merge`, which is the source tip of the last merge calculation and lags a push. Read a work item with `az boards work-item show --org … --id <n>`. Attachments in the description need auth to download: list them in the summary as not checked.

## Outside findings

- **Policies** — `az repos pr policy list --org … --id <id> -o json`: each evaluation's `status` (`approved`, `rejected`, `running`, `queued`) and `configuration.type.displayName` (Build, Status, Minimum number of reviewers). A `rejected` Build or Status is a failed check.
- **Build issues** — the ADO analogue of check annotations. The PR's builds: `az pipelines runs list <scope> --branch "refs/pull/<id>/merge" --top 5 -o json`. Their errors and warnings, with `data.sourcepath` and `data.linenumber` when the task gave them:

  ```bash
  az devops invoke --org https://dev.azure.com/<org> --area build --resource timeline --api-version 7.1 \
    --route-parameters project="<project>" buildId=<build-id> -o json \
    --query "records[].issues[] | [?type=='error' || type=='warning']"
  ```

- **Bot threads** — from `pullRequestThreads`: threads whose first comment's author is a bot (CodeRabbit, a scanner's service account), `status` `active` or `pending`, with `threadContext.filePath` and `rightFileStart.line`.
- **Sonar** — the PR's key for `pullRequest` is its `pullRequestId`.

## Post the review

ADO has no batched review: each inline comment is its own thread, and nothing is atomic. So:

1. Check every comment's line against `git diff -U0 origin/<target branch>...<head-oid> -- <path>` first; a line outside every hunk goes in the summary instead. ADO would accept it, but the rule holds on every forge.
2. Re-read the head (`pullRequestIterations`) right before posting; a head that moved since the review means the lines may not match — re-check the new commits before posting.
3. Post each thread from a `mktemp` file, then delete that exact path:

   ```json
   {"comments": [{"parentCommentId": 0, "commentType": 1, "content": "**Bug** — `rows` is undefined when …"}],
    "status": "active",
    "threadContext": {"filePath": "/src/export.ts",
                      "rightFileStart": {"line": 40, "offset": 1}, "rightFileEnd": {"line": 40, "offset": 1}}}
   ```

   ```bash
   az devops invoke <thread-route> --resource pullRequestThreads --http-method POST --in-file <file> -o json
   ```

   `filePath` starts with `/`. A deleted line uses `leftFileStart`/`leftFileEnd` with old-file numbers; a range sets start and end lines.
4. Post the summary last, as a thread with no `threadContext` and `"status": "closed"` — it asks for no action, so it mustn't hold a "resolve all comments" policy open. Its body names `Range: <base-oid>..<head-oid>` so a re-run finds the reviewed commit. Keep the `id` the POST returns: *Record fixes* writes the fix commits into this thread.

Never cast a vote (approve, reject, wait for author): the review runs under the user's account, and a vote is theirs.

A post that fails partway leaves the threads before it posted. Don't re-post them; post the rest and say so in the report.

## Record fixes

Write the fix commits into the summary thread: the one this run posted, by the `id` the POST in step 4 of posting returned (an earlier review's summary also has no `threadContext` and a `Range:` line, so don't look it up by those). Read its first comment's `content`, add or extend a `Fixed: <sha> …` line after the `Range:` line, and send it back:

```bash
# {"content": "<the whole summary, with the Fixed: line>"}
az devops invoke <thread-route> threadId=<summary-thread-id> commentId=1 --resource pullRequestThreadComments --http-method PATCH --in-file <file> -o json
```

## Fix and resolve

address-review-findings works only on GitHub, so do its loop here yourself, reading that skill for its rules (verdicts, commits, push safety, carrying fixes up a stack) but not its scripts. Per PR, stacks bottom-up:

1. Keep the review worktree from *Read a PR* after posting, and fix in it. Each posted finding and each bot thread you confirmed gets a fix; run the repo's checks again.
2. Call the Skill tool with "conventional-commit" to commit, and push with `git push origin HEAD:<source branch>`. A PR from a fork (`forkSource` set) pushes to `forkSource.repository.remoteUrl` instead; when that isn't writable, say so, leave its threads open, and stop fixing that PR.
3. Per thread — yours and the bots' you confirmed or disputed — reply, and resolve only when a fix landed:

   ```bash
   # reply: {"parentCommentId": 1, "commentType": 1, "content": "Fixed in abc1234: …"}
   az devops invoke <thread-route> threadId=<thread-id> --resource pullRequestThreadComments --http-method POST --in-file <file> -o json
   # resolve, only when a fix landed: {"status": "fixed"}
   az devops invoke <thread-route> threadId=<thread-id> --resource pullRequestThreads --http-method PATCH --in-file <file> -o json
   ```

   (`threadId=` joins the other `--route-parameters`.) A thread you disagree with gets a reply and stays `active`.
4. Record the fix commits (*Record fixes*).
5. In a stack, carry the fixes up before the next layer starts: merge the layer as pushed into the one stacked on it, in that layer's worktree, and push — merge, not rebase.
6. Remove the worktree once the PR's fixes are pushed and carried up: `git worktree remove --force <path> && rmdir <its parent>`.

A fix that changed what the PR describes → the "pr-body" skill, then `az repos pr update --org … --id <id> --description "<body>"` and `--title`.

## Ready to merge

`az repos pr show`'s `mergeStatus` is `succeeded` (`conflicts` or `failure` → not ready; `queued` → report as pending), every blocking policy evaluation (`configuration.isBlocking`) `approved` or `notApplicable` (`running`/`queued` → report as pending; a non-blocking one that's `rejected` is worth naming but doesn't block), no `active` or `pending` threads, and the target branch isn't another open PR's source branch. A release or develop branch is a fine target.
