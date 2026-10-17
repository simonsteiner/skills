---
name: attach-media
description: >
  Uploads local screenshots, images, GIFs, or screen recordings to GitHub and embeds them in a pull request, issue, or comment — the same attachment drag-and-drop makes in the web UI, no external hosting. Use when the user wants a screenshot or recording in a PR body, issue, or comment, asks to attach or embed an image on GitHub, or when a PR-body or review step has local before/after captures to show.
---

# Attach media

Since gh 2.99, `gh pr create|edit|comment` and `gh issue create|edit|comment` take `--attach`, which uploads the file and puts its URL in the body. That's the default path. A bundled script covers what `--attach` can't reach. `gh` must be authenticated (`gh auth status`).

## 1. Collect the files

Take only local paths the user gave or that this session produced (a screenshot just taken, a recording just rendered). A URL is already hosted: use it as is. No file, no upload — don't guess a path.

Accepted: png, jpg, jpeg, gif, webp, svg, mov, mp4, webm. Anything else (pdf, zip, logs) is refused; say so and offer to put a log's relevant lines in a fenced block instead. GitHub caps images at 10 MB and videos at 10 MB (100 MB on paid plans); downscale or trim a bigger capture first. Don't attach a capture that shows secrets, tokens, or personal data — crop or redact it: the upload can't be deleted, and it's public once a public body references it.

## 2. Write the body with local references

Reference each file by its local path where it explains something, and pass every file to `--attach`. gh uploads them, rewrites each `./path` to the uploaded URL, and appends any file the body doesn't reference.

```bash
cat > /tmp/shots/body.md <<'EOF'   # beside the captures, so ./before.png resolves
| Before | After |
|---|---|
| ![Settings page, text clipped](./before.png) | ![Settings page, text fits](./after.png) |

Walkthrough:

![](./flow.mp4)
EOF
cd /tmp/shots && gh pr edit 12 --body-file body.md --attach ./before.png --attach ./after.png --attach ./flow.mp4
```

- **Paths** in a `--body-file` resolve from that file's folder, so either write the body next to the captures or reference them by absolute path. With `--body`, they resolve from the working directory.
- **Alt text:** write what the image shows, not the file name. For an appended file give it after `#`: `--attach './login.png#The login error state'`.
- **Video:** `![](./flow.mp4)` alone in its paragraph becomes the bare URL GitHub renders as a player; anywhere else it degrades to a link. A bare `./flow.mp4` line is not a reference and stays as written.
- **Not rewritten:** paths inside code spans or fences, and HTML `<img src>`. Use Markdown references.
- **Existing body:** `gh pr edit <n> --attach <file>` with no body flag keeps the body and appends the file. To place it inside the existing text, fetch the body (`gh pr view <n> --json body --jq .body > /tmp/body.md`), add the reference, and pass `--body-file`.
- **Partial failure:** what uploaded is still written, the command exits non-zero, and the error names the file. Fix that file and attach it with a second edit — don't rerun the whole command, which uploads every file again.

When this is a step in writing a PR body, hand the body back to that step with the `--attach` flags it needs, rather than posting it yourself.

## 3. Fall back to the script

`--attach` uploads to the PR's or issue's own repository and needs write access there, and only those six commands have it. Use the script when:

- gh is older than 2.99 (`gh --version`);
- the PR is from a fork into a repo you can't push to: upload to your fork with `--repo <you>/<fork>`, and the URL still renders in the upstream PR;
- the target has no `--attach`: `gh pr review`, a review-thread reply, or a body sent through `gh api`.

```bash
<skill-dir>/scripts/upload.sh [--repo OWNER/REPO] <file>...
```

It checks every file before uploading any, then prints one Markdown line per file in argument order: `![name](url)` for an image, a bare URL for a video. Swap in real alt text before placing the line. A 404 means no write access to that repo.

## 4. Check it rendered

Fetch the body back (`gh pr view <n> --json body --jq .body`) and confirm no `./path` reference is left; one left over means its file wasn't passed to `--attach`.

See [CREDITS.md](CREDITS.md) for where this comes from.
