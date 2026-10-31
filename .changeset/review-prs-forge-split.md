---
"simonsteiner-skills": patch
---

review-prs: a new `scripts/forge.sh` picks the forge from `origin` alone (Azure DevOps hosts first, then GitHub, then any host `gh` accepts), so a `GH_REPO` or a GitHub `upstream` remote no longer decides it. The GitHub and Azure DevOps guides now share the same sections, each forge's fix loop lives in its own guide, and the Azure DevOps guide is marked untested: it stops on an error rather than guess. The GitHub path is unchanged.
