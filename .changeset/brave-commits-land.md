---
"simonsteiner-skills": minor
---

`conventional-commit` now makes the commits instead of stopping at the message. It triggers before any `git commit` — "commit", "commit and push", "commit in logical chunks", or a commit step inside another workflow — rather than only when a message is asked for, which is why it had loaded for 3 of roughly 400 agent commits and most bodies came out hard-wrapped. A mixed worktree is committed as several atomic commits staged by path, the message goes through a quoted heredoc, and the result is checked for wrapped bodies before pushing. Asking for just a message still returns one.
