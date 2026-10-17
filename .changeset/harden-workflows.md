---
"simonsteiner-skills": patch
---

CI workflows are hardened: actions are pinned by commit SHA (kept current by Dependabot), the lint workflow declares a read-only token and doesn't keep git credentials, and the changelog job, which can push to `main`, installs dependencies without running their install scripts.
