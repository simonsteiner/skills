---
"simonsteiner-skills": patch
---

review-prs paraphrases what a diff does from the code alone and flags a PR body that claims more, or less, than the diff shows. It searches the repo for an existing helper before accepting a new one, and reports a review sub-agent that fails twice as not reviewed instead of clean. It disagrees with a finding, its own or a bot's, only with evidence a reader can check, and leaves that thread open for the user. A finding posted as the user's call waits for their answer. The skill is now self-contained: it carries its own rules for weighing and disagreeing, and tells resolved bot threads apart with its own `review-threads.sh`. With no sub-agent tool it reviews in the thread's context and says so. In T3 Code, review sub-agents run through `delegate_task` with `isolation: "worktree"`, which avoids the permission-prompt timeouts an out-of-workspace `mktemp` worktree hit under Antigravity. Adapted from Google's Elephant-Goldfish Model.
