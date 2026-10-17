---
"simonsteiner-skills": minor
---

New model-invoked `attach-media` skill: embeds local screenshots, GIFs, and screen recordings in a PR, issue, or comment with no external hosting. It uses gh's own `--attach` (gh 2.99+) and covers what that can't reach — older gh, PRs from a fork, review comments, `gh api` bodies — with a bundled upload script. `pr-body` now calls it to embed screenshots as evidence.
