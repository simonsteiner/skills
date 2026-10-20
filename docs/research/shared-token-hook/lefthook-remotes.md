# Question 1: lefthook `remotes:`

Part of [the shared token hook research](README.md). Version: **lefthook v2.2.2**, the latest release (published 2026-10-13) per the [GitHub releases list](https://github.com/evilmartians/lefthook/releases). Source links point at tag `v2.2.2` (commit `eb4e504`). Experiments (letters) are in [experiment-log.md](experiment-log.md).

## Syntax and where remotes live

```yaml
remotes:
  - git_url: https://github.com/org/repo   # or git@…, or file:///path/to/bare.git (used in the experiment)
    ref: v1.0.0                            # optional; a branch or tag
    configs: [path/from/remote/root.yml]   # optional; default [lefthook.yml]
    refetch: false                         # optional; true = fetch on every run
    refetch_frequency: 24h                 # optional; always | never | duration
```

- `git_url` is "accessed with privileges of the machine lefthook runs on" ([git_url.md](https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/configuration/git_url.md)). `ref` is "An optional *branch* or *tag* name" ([ref.md](https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/configuration/ref.md)). `configs` defaults to `[lefthook.yml]` and holds "config paths from remote's root" ([configs.md](https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/configuration/configs.md)).
- `refetch_frequency`: when unset or `never`, lefthook "will not fetch from remote" again. "Failure to fetch does not cause an error, but just a warning message. If a successfully fetched previous configuration exists, it will be used. Otherwise, the remote will be ignored." `refetch: true` overrides it ([refetch_frequency.md](https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/configuration/refetch_frequency.md), [refetch.md](https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/configuration/refetch.md)). An immutable tag needs neither.
- **Location**: `<git info dir>/lefthook-remotes/<repo-name>[-<ref>]`, where the info dir comes from `git rev-parse --path-format=absolute --git-path info` ([git/remote.go#L10-L24](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/git/remote.go#L10-L24), [wrapper/paths.go#L7-L14](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/git/wrapper/paths.go#L7-L14)). In a ref, `-` becomes `--` and `/` becomes `-` ([remote.go#L58-L83](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/git/remote.go#L58-L83)). Seen: `.git/info/lefthook-remotes/remote-file--tokens--v1.2.0`. A linked worktree shares the main clone's copy (experiment K).

## Running a script that lives in the remote: yes

- Docs: with `scripts` in a remote config, "the script `source_dir` must also be in the **root of the remote repository**" ([remotes.md](https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/configuration/remotes.md)). Scripts are "your own executables which are being run in the project root" ([Scripts.md](https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/configuration/Scripts.md)).
- Source: the script search path is the repo's `source_dir`, `source_dir_local`, `.config/lefthook{,-local}`, and **`<remote clone>/<the consumer's source_dir>` for every remote** ([command/run.go#L197-L222](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/command/run.go#L197-L222)). A `script:` job runs `<runner> '<sourceDir>/<hook>/<script>' <args>` for **each** source dir where the file exists. It makes the file executable if needed, and with `args:` it expands templates such as `{staged_files}` ([build_script.go#L47-L91](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/run/controller/command/build_script.go#L47-L91)). `args:` arrived in 2.0.5 ([args.md](https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/configuration/args.md)).
- So the job can be defined in the **consumer's** `lefthook.yml` and still find the remote's script: the lookup doesn't care which config declared the job.
- Verified (experiment 1, D): cwd = consumer root; script path = `…/.git/info/lefthook-remotes/remote-v1.0.0/.lefthook/pre-commit/probe.py`; argv = `['b.md', 'lefthook.yml', 'sub/a file.txt']` (a filename with a space arrives as one argument). The real script blocked an 8,106-token file with its split instructions. A symlinked script in the remote works too (experiment M; on Windows, git may check symlinks out as plain files, **Unverified**).
- Not needed: pointing `run:` at `.git/info/lefthook-remotes/…`. There's no template for the remote path ([run.md](https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/configuration/run.md) lists `{files}`, `{staged_files}`, `{push_files}`, `{all_files}`, `{cmd}`, `{lefthook_job_name}`), and the path depends on the `.git` layout. `script:` is the supported route.
- Caveat: the remote path uses the *consumer's* `source_dir` (default `.lefthook/`). A repo that changes `source_dir` won't find the script.

## Clone depth and size

- Clone: `git -C <info>/lefthook-remotes clone --quiet --origin origin --depth 1 [--branch <ref>] <url> <dir>`, then `fetch --depth 1 origin -- <ref>` and `checkout FETCH_HEAD` ([wrapper/clone.go#L14-L18](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/git/wrapper/clone.go#L14-L18), [wrapper/fetch.go#L7-L17](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/git/wrapper/fetch.go#L7-L17)). Shallow, but not sparse: the whole tree at that ref.
- `simonsteiner/skills` is public. `git clone --depth 1` takes 0.56 s and 1.1 MB on disk (103 files). The full local pack is 408 KiB; `git count-objects -vH` reports `size-pack: 408.34 KiB`. Measured 2026-10-20. That's paid once per ref per clone, so a dedicated repo would save next to nothing. It would also make a second copy of the script, the drift this is meant to end.
- Because `--branch` is used, **`ref:` can't be a commit SHA**: the clone fails (`exit status 128`), and on `run` lefthook falls back to any cached ref of the same repo with a warning, `Will continue with fallback version: v1.1.0` (experiment E; [install.go#L169-L184](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/command/install.go#L169-L184), [#L268-L287](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/command/install.go#L268-L287)).

## Install vs run, offline, cloud and CI

- `lefthook install` syncs every remote; on failure it warns `Couldn't sync from <url>. Will continue anyway` and installs hooks from what it has ([install.go#L44-L68](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/command/install.go#L44-L68)).
- Every hook run (`git commit`, `lefthook run`) calls `syncHooks`. That fetches a remote only when `shouldRefetch` says so: `refetch`/`always`, or **no `.git/FETCH_HEAD` in the expected `<name>-<ref>` dir** (first use or a new `ref`), or `refetch_frequency` elapsed. Then it deletes remote dirs that no longer match any configured ref ([run.go#L101-L111](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/command/run.go#L101-L111), [install.go#L159-L232](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/command/install.go#L159-L232), [#L234-L266](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/command/install.go#L234-L266)).
- Offline after the first fetch: no network needed, since a pinned tag never refetches (experiment F: bare repo moved away, commit passed).
- Fresh clone, remote unreachable:
  - **Job in the consumer's `lefthook.yml`**: the pre-commit hook is installed, and each commit retries the clone. Until it succeeds the commit **fails** with `script does not exist: check-file-tokens.py` (fail-closed, experiment G). Once the remote is back, the next commit fetches and passes, with no reinstall.
  - **Job only in the remote config**: `lefthook install` finds no hooks, so **no pre-commit hook is installed at all**, and an oversized file commits cleanly (experiment H). It stays that way until someone reruns `lefthook install` (experiment J). That's why the recommendation keeps the job in each repo.
- claude.ai/code cloud sessions: a fresh Ubuntu 24.04 VM with your repo cloned, Python 3.x with uv, Node 20–22 with npm/pnpm, and Rust ([Installed tools](https://code.claude.com/docs/en/cloud-environments#installed-tools)). lefthook isn't listed: hooks exist only if the repo's setup installs them (Node `prepare` on `npm install`, or a SessionStart hook). GitHub traffic goes through a proxy that serves *API* requests and archive downloads only for repos attached to the session (others get 403, "even a public one"). `raw.githubusercontent.com` stays reachable ([GitHub proxy](https://code.claude.com/docs/en/cloud-environments#github-proxy)). **Unverified**: whether `git clone https://github.com/simonsteiner/skills` from a session attached only to another repo succeeds. If it doesn't, commits fail with `script does not exist` (fail-closed). The fix would be attaching `simonsteiner/skills` to the session, or a setup script.
- CI: hooks don't run unless a workflow calls `lefthook run`. If one does, it needs network access to GitHub once per job. Python is preinstalled on GitHub-hosted Ubuntu runners (see [runners.md](runners.md)).

## Merging and overriding

- Order: `lefthook.yml` → `extends` → `remotes` → `lefthook-local.yml`; "`remotes` override `extends`, and `lefthook-local.yml` can override everything" ([extends.md](https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/configuration/extends.md); [loader.go#L154-L200](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/config/loader.go#L154-L200)). A remote's own `extends` paths resolve against the remote root ([loader.go#L287-L330](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/config/loader.go#L287-L330)). A remote can't set the `lefthook` key ([loader.go#L180-L181](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/config/loader.go#L180-L181)).
- `jobs:` merge **by `name:`**: a later layer's keys overwrite the earlier layer's, keys it doesn't set survive, and unnamed jobs are appended ([loader.go#L612-L701](https://github.com/evilmartians/lefthook/blob/v2.2.2/internal/config/loader.go#L612-L701), `maps.Merge(srcJob, destJob)` at L677). `commands:` are a map keyed by name and merge the same way. Verified with `lefthook dump`:
  - A: remote defines job `file-tokens` with `args: --max-tokens 5000 …`. The repo's `lefthook.yml` sets `args: --max-tokens 100 …` on the same name → **remote wins (5000)**.
  - B: the repo's `lefthook.yml` sets `skip: true` → kept, because the remote doesn't set `skip`, so a repo *can* skip a remote job.
  - C: `lefthook-local.yml` sets `args: --max-tokens 100 …` → **local wins (100)**. But that file is per-machine and git-ignored ([local.md](https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/usage/features/local.md)).
- So with the job in the remote, a repo can't change the budget in a committed file. With the job in the repo and only the script in the remote (experiment D), the repo owns `args:` outright. `skip:` ([skip.md](https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/configuration/skip.md)) and `LEFTHOOK=0` still work.

## Version bumps and Renovate/Dependabot

- Bump = edit `ref:`. The next hook run sees no `FETCH_HEAD` for the new ref, clones it, and deletes the stale dir (experiment D: v1.0.0 → v1.1.0, `remote-v1.0.0` removed). The `ref.md` note says not to drop `ref:` once used.
- Renovate: no lefthook manager in [the managers list](https://docs.renovatebot.com/modules/manager/). The fallback is a [custom regex manager](https://docs.renovatebot.com/modules/manager/regex/) with the [`github-tags`](https://docs.renovatebot.com/modules/datasource/github-tags/) or [`git-tags`](https://docs.renovatebot.com/modules/datasource/git-tags/) datasource. For prefixed tags, [regex versioning](https://docs.renovatebot.com/modules/versioning/regex/) has a `compatibility` group that Renovate never changes. **Unverified (not run)**:

  ```json
  {
    "customManagers": [{
      "customType": "regex",
      "managerFilePatterns": ["/(^|/)lefthook\\.ya?ml$/"],
      "matchStrings": ["git_url: https://github\\.com/(?<depName>simonsteiner/skills)\\s+ref: (?<currentValue>\\S+)"],
      "datasourceTemplate": "github-tags",
      "versioningTemplate": "regex:^(?<compatibility>file-tokens)-v(?<major>\\d+)\\.(?<minor>\\d+)\\.(?<patch>\\d+)$"
    }]
  }
  ```

- Dependabot: no lefthook ecosystem and no generic/regex updater in [supported ecosystems](https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories) (`pre-commit`, `gitsubmodule`, `uv`, `npm`, `cargo` and others are listed). A scripted `gh` loop is the dependable way to bump across 22 repos.
