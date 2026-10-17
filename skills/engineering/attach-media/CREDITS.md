# Credits

- gh's own `--attach` flag (cli/cli, since v2.99.0) is the default path; its `internal/attachments` package documents how local references are rewritten, which section 2 follows.
- `attach-github-assets` from <https://github.com/intercom/2x-skills> (MIT): found that the web UI's `uploads.github.com/user-attachments/assets` endpoint takes a `gh` token, and the image vs. video Markdown split. This skill's fallback script is a rewrite. It goes through `gh api`, so it handles no token itself; it checks every file before it uploads any, and it takes more than one file in a single call.
- Ben Sheldon, [Programmatically upload attachments to GitHub Issues, Pull Requests, and Comments](https://island94.org/2026/08/programmatically-upload-attachments-to-github-issues-pull-requests-comments), which wrote the endpoint up.

Behaviour checked against github.com on 2026-10-17. It needs push access to the repo (a 404 otherwise), accepts only png/jpeg/gif/webp/svg/mov/mp4/webm (and rejects pdf, zip, txt, json), and keeps an upload private until a body references it.

---

MIT License

Copyright (c) 2026 Intercom

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
