---
"simonsteiner-skills": patch
---

review-prs: called as a thread's first message, it now reviews every open PR that needs a review, even when the thread sits on a PR's branch, and links them to the thread. Called partway through a thread, it narrows to that thread's linked PRs or its current branch; a branch with no PR now gets a local review against the default branch, and a thread on the default branch stops instead of reviewing every open PR.
