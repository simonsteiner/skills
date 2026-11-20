---
"simonsteiner-skills": patch
---

conventional-commit, pr-body and sync-and-branch describe the asks they cover the way people phrase them: a commit or PR that is one step of a bigger request ("commit and open a PR", "commit directly to main", "push and open a PR"), and work that should land on a new branch, including one stacked on a named base. conventional-commit and pr-body also say to load them even for a commit or PR that looks too simple to need them, which is where most misses were. sync-and-branch now cuts from a base the user names and writes the default branch's name into later commands instead of a shell variable that doesn't survive between tool calls. conventional-commit uses `mktemp` for its hunk patch and states the no-hard-wrap rule once. All three gain evals.
