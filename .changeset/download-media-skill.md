---
"simonsteiner-skills": minor
---

New model-invoked `download-media` skill: downloads the screenshots, recordings, and files attached to issues, PRs, and review comments — private repos included, where the URLs 404 without auth — so the agent can look at them, pulling frames out of recordings with ffmpeg. `address-review-findings` and `review-prs` now call it when a thread or PR body carries media.
