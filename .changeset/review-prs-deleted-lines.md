---
"simonsteiner-skills": patch
---

`review-prs` can now comment on deleted lines. Its `post-review.sh` checked every comment against new-file line numbers only, so a `"side": "LEFT"` comment on a removed line or a deleted file was rejected as outside the diff, while a LEFT comment on a line number that existed only on the new side passed and made GitHub reject the whole review. It also failed comments on files whose path holds a space or a non-ASCII character. Each end of a comment is now checked against its own side, within one hunk.
