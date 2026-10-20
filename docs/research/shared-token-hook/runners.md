# Question 2: running the script outside lefthook remotes

Part of [the shared token hook research](README.md). Measurements were taken on 2026-10-20 on WSL2 Ubuntu with uv 0.12.22, npm 11.16.0 and Node 24.18.0, after a warm-up run; the commands are in [experiment-log.md](experiment-log.md#uv-npm-and-python-runs).

## Measured: per-commit cost and offline behaviour

| How it runs | Warm run | Offline, cache warm | Needs on the machine |
| --- | --- | --- | --- |
| `python3 <script>` (lefthook remote or a copy) | 0.03 s | works | python3 |
| `uvx file-tokens@1.0.0` (PyPI, exact pin; measured with `cowsay@6.1`) | 0.04 s | works (`UV_OFFLINE=1`) | uv |
| `uvx --from git+https://…@<commit SHA>` (GitHub) | 0.06 s | works | uv, git |
| `uvx --from git+https://…@<tag>` (GitHub) | **0.81–0.84 s** | **fails** | uv, git, network |
| `python3` + a file fetched from `raw.githubusercontent.com/<owner>/<repo>/<SHA>/…` into `.git/` | 0.03 s cached; 0.27 s first fetch | works once fetched | python3, a fetch step |
| `npx --yes git+file://…#<tag or SHA>` | 0.36–0.40 s | **fails, exit 128, no message** | Node, git, network |

- **uvx with a git tag** runs `git fetch` for the tag on every run, even when warm, and with `UV_OFFLINE=1` it fails: `Remote Git fetches are not allowed because network connectivity is disabled`. With a full **commit SHA** it ran from cache, offline too. The [uv cache docs](https://docs.astral.sh/uv/concepts/cache/) say "For Git dependencies, uv caches based on the fully-resolved Git commit hash", so a tag has to be resolved first. `UV_OFFLINE` "will disable network access" ([env reference](https://docs.astral.sh/uv/reference/environment/)). The [tools guide](https://docs.astral.sh/uv/guides/tools/) documents `--from git+…@tag` and `@commit`, and that `tool@version` takes "an exact version" only.
- **uvx from PyPI, exact version**: the verbose log showed `Found fresh response for: https://pypi.org/simple/cowsay/`, so it uses the HTTP cache while that's fresh and worked with `UV_OFFLINE=1`. The [tools concept page](https://docs.astral.sh/uv/concepts/tools/) says uvx keeps "the cached version of the tool unless a different version is requested". It doesn't say when the index is re-checked.
- **npx with a git spec** needed the git source on every run in the test, even for a SHA and with `--offline`, and exited 128 without printing anything. The [npm exec docs](https://docs.npmjs.com/cli/v11/commands/npm-exec) describe `--offline` ("Any packages not locally cached will result in an error") and `--prefer-offline`, and say nothing about git specs. [package.json docs](https://docs.npmjs.com/cli/v11/configuring-npm/package-json#git-urls-as-dependencies) allow `git+https`/`git+file` URLs with `#<commit-ish>` or `#semver:<range>`, and GitHub shorthand `user/repo#ref`. So a pinned git dependency works as a **devDependency** (lockfile, `node_modules/.bin`), not as a per-commit `npx` fetch. **Unverified**: offline `npm ci` with a git devDependency.
- **pipx run** caches each run environment for 14 days, then "the next run fetches the latest version". With the uv backend, "uv's own cache applies instead" ([pipx: running applications](https://pipx.pypa.io/stable/tutorial/run-applications.html)). An unpinned spec moves on its own, and pipx is one more tool to install. Not measured.
- **python3 + a fetched file**: a job (or a small wrapper) downloads the script once from a pinned raw URL into `.git/` (e.g. `.git/file-tokens/<SHA>.py`) and runs it with `python3` after that. A full SHA in the URL makes the pin immutable, unlike a tag; the first fetch took 0.27 s, and GitHub serves raw files with `cache-control: max-age=300` (measured 2026-10-20). After that it's a local file: offline-safe, same cost as a copy. `raw.githubusercontent.com` is on the cloud sessions' Trusted list ([cloud environments](https://code.claude.com/docs/en/cloud-environments#github-proxy)), so it sidesteps the **Unverified** cloud-clone question. Costs: the fetch-and-cache logic has to live somewhere in each repo's `lefthook.yml` (a shell one-liner with `curl`, which native Windows may lack, or `python3 -c` with `urllib`), it's fail-closed only if written that way, and nothing checks the download's integrity beyond the SHA in the path. Bumps are a SHA change, which Renovate's regex manager can do with the `git-refs` datasource (**Unverified**: not run). The wrapper itself is not tested end to end here.
- **pnpm dlx**: the [dlx docs](https://pnpm.io/cli/dlx) say nothing about git specs, caching or offline use. **Unverified**.

## Per stack

| Stack | Already has | Best fit |
| --- | --- | --- |
| Python (uv) | uv, Python, lefthook as a dev dependency | lefthook remote + `python3`; or `uvx file-tokens@X.Y.Z` once on PyPI |
| Node (npm/pnpm, Astro) | Node; lefthook via npm; usually python3 on dev machines (below) | lefthook remote + `python3`. A Node port would be a second implementation to keep in sync, and an npm package wrapping the Python script still needs python3 |
| Rust, Rust+Python (maturin) | cargo; maturin repos have Python/uv | lefthook remote + `python3` |
| Docs/config only | lefthook from wherever it was installed | lefthook remote + `python3` |

## Can bare `python3` be assumed?

- **macOS**: no Python ships with the OS. Apple DTS: "macOS does not come with a built-in copy of Python" ([Apple Developer Forums 790807](https://developer.apple.com/forums/thread/790807)). [Python's macOS guide](https://docs.python.org/3/using/mac.html): `/usr/bin/python3` "links to a usually older and incomplete version of Python provided by and for use by the Apple development tools, Xcode or the Command Line Tools for Xcode". Without the Command Line Tools, running it brings up the install prompt (thread 790807's question). A Mac that runs `git` from Apple's tools has the Command Line Tools and so a `python3`. That's an inference, **Unverified** against an Apple doc. The script ran unchanged on Python 3.9 (tested); Apple's CLT version is **Unverified**.
- **Windows**: the `windows-2025` runner image lists Python 3.12.10 and cached 3.10–3.14 ([Windows2025-VS2026 readme](https://github.com/actions/runner-images/blob/main/images/windows/Windows2025-VS2026-Readme.md)). Whether a `python3` command (not `python`) is on PATH there or on dev machines is **Unverified**. WSL is Linux: the distro's Python (Ubuntu ships `python3`; this machine has `/usr/bin/python3`).
- **GitHub Actions**: `ubuntu-24.04` lists Python 3.12.3, Pipx 1.16.7, Node 22.23.3 and npm 10.9.9. uv, pnpm and lefthook are not listed ([Ubuntu2404 readme](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md), image 20261012). [runner-images](https://github.com/actions/runner-images) installs "5 most popular `major.minor` versions" of Python.
- **Claude Code cloud sessions**: "Python 3.x with pip, poetry, uv, black, mypy, pytest, ruff"; Node 20/21/22 with npm, yarn, pnpm; Rust; git and gh; Ubuntu 24.04 x86_64. PyPI, `files.pythonhosted.org` and `registry.npmjs.org` are reachable on the default Trusted level ([cloud environments](https://code.claude.com/docs/en/cloud-environments#installed-tools)).

**Conclusion**: `python3` ≥ 3.9 is a safe assumption on Linux, WSL, CI runners and cloud sessions, and on Macs with the Command Line Tools installed (that every Mac with git has them is **Unverified**, above). Native Windows is the gap, and it's the same gap the copied script has today. uv is guaranteed only in the uv repos and in cloud sessions, so `uvx` would add a requirement to Node, Rust and docs repos. The lefthook remote doesn't.

## Runner-up: publish to PyPI and run with `uvx`

If the lefthook remote turns out not to clone in cloud sessions (**Unverified**, see [lefthook-remotes.md](lefthook-remotes.md#install-vs-run-offline-cloud-and-ci)), there are two fallbacks. The cheapest is **python3 + a fetched file** (above): no new tool, and `raw.githubusercontent.com` is reachable in cloud sessions, but each repo carries the fetch logic. The cleaner one is a PyPI package with an exact pin:

```yaml
pre-commit:
  jobs:
    - name: file-tokens
      run: uvx file-tokens@1.0.0 --max-tokens 5000 {staged_files}
```

That gives 0.04 s warm, offline once cached, and PyPI is reachable in cloud sessions. Renovate can bump it with a regex manager and the `pypi` datasource. Costs: uv on every machine (a new requirement for Node, Rust and docs repos), a PyPI name, and a release workflow. Never `uvx --from git+…@<tag>`: it fetches on every commit and fails offline.
