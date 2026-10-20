# Experiment log

Part of [the shared token hook research](README.md). Run on 2026-10-20 in `/tmp/lhx` (WSL2 Ubuntu, git, Python 3.14 as `python3`), all throwaway. Outputs are trimmed, and colour codes and box art are removed. `W=/tmp/lhx/exp`; `NO_COLOR=1` was set.

## Setup

```bash
# lefthook binary, downloaded into its own empty dir; checksum matches lefthook_checksums.txt
gh release download v2.2.2 -R evilmartians/lefthook -p 'lefthook_2.2.2_Linux_x86_64' -p 'lefthook_checksums.txt'
sha256sum lefthook_2.2.2_Linux_x86_64   # 4fbf89eb…f2800b6, same as the checksums file
cp lefthook_2.2.2_Linux_x86_64 /tmp/lhx/bin/lefthook && lefthook version   # 2.2.2

# The remote: a bare repo, pushed from a work tree holding
#   lefthook.yml                              jobs file-tokens (script, runner python3, args "--max-tokens 5000 {staged_files}") and probe
#   .lefthook/pre-commit/check-file-tokens.py the skill's script
#   .lefthook/pre-commit/probe.py             prints cwd, __file__, argv
git init --bare $W/remote.git;  …commit…;  git tag v1.0.0;  git push origin HEAD:main --tags

# The consumer
mkdir consumer && cd consumer && git init
printf 'remotes:\n  - git_url: file://%s/remote.git\n    ref: v1.0.0\n' $W > lefthook.yml
lefthook install            # sync hooks: ✔️(pre-commit)
ls .git/info/lefthook-remotes/                # remote-v1.0.0  (a depth-1 clone: one commit in its log)
```

## 1. Remote script runs, gets `{staged_files}`

```text
$ echo hi > "sub/a file.txt"; echo x > b.md; git add -A; git commit -m test
┃  probe ❯
PROBE cwd= /tmp/lhx/exp/consumer
PROBE script= /tmp/lhx/exp/consumer/.git/info/lefthook-remotes/remote-v1.0.0/.lefthook/pre-commit/probe.py
PROBE argv= ['b.md', 'lefthook.yml', 'sub/a file.txt']
✔️ probe (0.01 seconds)
✔️ file-tokens (0.04 seconds)

$ head -c 24000 /dev/urandom | base64 > big.txt; git add big.txt; git commit -m big   # exit 1
File token limit: 1 staged file is over 5,000 tokens (bytes / 4).
  big.txt    8,106 tokens  (3,106 over; split into 3+ files)
…split instructions…
```

## A–C. Merge precedence (`lefthook dump`)

The remote's job sets `args: --max-tokens 5000 {staged_files}`.

| Case | Override written | `dump` result for `file-tokens` |
| --- | --- | --- |
| A | `lefthook.yml`: `jobs: [{name: file-tokens, args: "--max-tokens 100 {staged_files}"}]` | `args: --max-tokens 5000 …` (remote wins) |
| B | `lefthook.yml`: `jobs: [{name: file-tokens, skip: true}]` | remote job plus `skip: true` |
| C | `lefthook-local.yml`: same `args` as A | `args: --max-tokens 100 …` (local wins) |

## D. Consumer-owned job, script from the remote, ref bump

The remote gets `scripts-only.yml` (just `min_version: 2.0.5`) and is tagged `v1.1.0`. In the consumer:

```yaml
remotes:
  - git_url: file:///tmp/lhx/exp/remote.git
    ref: v1.1.0
    configs: [scripts-only.yml]
pre-commit:
  jobs:
    - name: file-tokens
      script: check-file-tokens.py
      runner: python3
      args: "--max-tokens 100 {staged_files}"
```

```text
$ git commit -m D          # no `lefthook install` after changing ref
File token limit: 2 staged files are over 100 tokens (bytes / 4).
✗ file-tokens (0.04 seconds)
$ ls .git/info/lefthook-remotes/
remote-v1.1.0              # v1.1.0 fetched by the commit; remote-v1.0.0 deleted
```

## E. `ref:` set to a commit SHA

```text
$ lefthook install
│  Couldn't sync from file:///tmp/lhx/exp/remote.git. Will continue anyway: exit status 128
$ lefthook run pre-commit
│  Couldn't sync file:///tmp/lhx/exp/remote.git 8fd0e4e…877. Will continue with fallback version: v1.1.0.
✓ file-tokens (0.04 seconds)
```

## F–J. Remote unreachable (`mv remote.git remote.git.off`)

```text
# F: clone already present, ref pinned → no fetch, commit passes
✓ file-tokens (0.04 seconds)

# G: fresh `git clone consumer consumer2` (job in consumer's lefthook.yml)
$ lefthook install
│  Couldn't sync from file:///tmp/lhx/exp/remote.git. Will continue anyway: exit status 128
sync hooks: ✔️(pre-commit)
$ git commit -m G          # exit 1
│  Couldn't sync from file:///tmp/lhx/exp/remote.git. Will continue without that remote.
✗ file-tokens: script does not exist: check-file-tokens.py
# …remote restored, next commit in consumer2: fetched, ✓ file-tokens (no reinstall)

# H: fresh repo whose lefthook.yml has only `remotes:` (jobs only in the remote)
$ lefthook install
│  Couldn't sync from file:///tmp/lhx/exp/remote.git. Will continue anyway: exit status 128
sync hooks: ✔️                # no hook names: nothing installed
$ git add big.txt (7,500 tokens); git commit -m H       # exit 0, no hook ran
# remote restored, another commit: still exit 0 (no .git/hooks/pre-commit)

# J: rerun `lefthook install` → sync hooks: ✔️(pre-commit); next commit blocked:
  big.txt    7,501 tokens  (2,501 over; split into 3+ files)
✗ file-tokens (0.04 seconds)
```

## K. Worktree

```text
$ git worktree add ../wt -b wt; cd ../wt; git commit …
✓ file-tokens (0.04 seconds)      # uses ../consumer2/.git/info/lefthook-remotes/remote-v1.1.0; no copy per worktree
```

## L. Run only the token job (for arch-review)

```text
$ LEFTHOOK=0 git commit -m "2,000-byte mid.txt"
$ lefthook run pre-commit --job file-tokens --all-files
  mid.txt      500 tokens  (400 over; split into 7+ files)
✗ file-tokens (0.04 seconds)
$ lefthook run pre-commit --job file-tokens --file c.md --file mid.txt
  mid.txt      500 tokens  (400 over; split into 7+ files)
```

## M. Symlinked script, prefixed tag

In the remote, the script moves to `skills/engineering/setup-lefthook/scripts/check-file-tokens.py`, and `.lefthook/pre-commit/check-file-tokens.py` becomes a symlink to it (`git ls-files -s` shows mode `120000`). The commit is tagged `file-tokens-v1.2.0`.

```text
$ sed -i 's/ref: v1.1.0/ref: file-tokens-v1.2.0/' lefthook.yml
$ lefthook run pre-commit --job file-tokens --file c.md --file mid.txt
  mid.txt      500 tokens  (400 over; split into 7+ files)
$ ls .git/info/lefthook-remotes/
remote-file--tokens--v1.2.0
```

## N. `commands:` and `jobs:` in one hook

Adding `commands: {echo-cmd: {run: echo CMD-RAN {staged_files}}}` beside the `jobs:` list: `lefthook validate` → `All good`; `lefthook run pre-commit --file c.md` → `CMD-RAN c.md`, `✓ file-tokens`, `✓ echo-cmd`.

## Clone size of `simonsteiner/skills`

```text
$ git count-objects -vH            # this worktree's repo
size-pack: 408.34 KiB
$ time git clone -q --depth 1 https://github.com/simonsteiner/skills.git   # 0.56 s
$ du -sh skills skills/.git; git -C skills ls-files | wc -l
1.1M skills   103
$ gh api repos/simonsteiner/skills/tags     # [] — no tags yet
```

## uv, npm and Python runs

`UV_CACHE_DIR` and `npm_config_cache` were pointed at fresh dirs under `/tmp/lhx`. The local package `file-tokens` wraps the script with a `check-file-tokens` entry point and is tagged `v1.0.0`.

```text
uvx --from git+file:///tmp/lhx/uvexp/pkg@v1.0.0 check-file-tokens c.md     cold 0.36 s, warm 0.06–0.07 s
uvx -v … @v1.0.0                       DEBUG Performing a Git fetch for: file:///tmp/lhx/uvexp/pkg   (every run)
source dir moved away, @v1.0.0 (UV_OFFLINE=1 or not)   error: … failed to fetch branch or tag `v1.0.0`
source dir moved away, @<SHA> (UV_OFFLINE=1 or not)    rc=0 (served from cache)
python3 …/cli.py c.md                                  0.03 s

R=https://github.com/theskumar/python-dotenv; tag v1.1.1 = 16e660d…448
uvx --from git+$R@v1.1.1 dotenv …      warm 0.84 / 0.81 / 0.81 s
uvx --from git+$R@16e660d…448 dotenv … warm 0.06 / 0.06 / 0.06 s; UV_OFFLINE=1 0.06 s
UV_OFFLINE=1 uvx --from git+$R@v1.1.1  cause: Remote Git fetches are not allowed because network connectivity is disabled (i.e., with `--offline`)
(the dotenv CLI itself exited 1 for a missing extra; the timing is of uvx starting it)

uvx cowsay@6.1 -t hi                   warm 0.04 s ×3; UV_OFFLINE=1 0.04 s; -v: "Found fresh response for: https://pypi.org/simple/cowsay/"

npx --yes git+file:///tmp/lhx/npmexp/pkg#v1.0.0 a.md   cold 0.65 s, warm 0.39–0.40 s;  #<SHA> warm 0.36 s
source moved away: npx --yes --offline …#<SHA> → exit 128, no output;  npx --yes …#v1.0.0 → exit 128

python3.9 -I check-file-tokens.py --max-tokens 100 c.md mid.txt   → works on 3.9 (rc=1, mid.txt listed)
```
