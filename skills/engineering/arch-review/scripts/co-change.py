#!/usr/bin/env python3
"""List the pairs of files that keep changing in the same commit.

    co-change.py [--since 6.months] [--top 30] [--min 3] [--max-files 30] [<path>...]
    co-change.py --help

Run inside a git repo. Walks the commits since --since (a date or a relative time
such as `6.months` or `2026-01-01`) on the current branch, skipping merges, and counts
every pair of files changed together. A commit touching more than --max-files files in
the whole repo (a rename sweep, a formatter run) says nothing about coupling and is
skipped, whatever the paths. With paths (relative to the current directory), only
files under them count. Files that no longer exist are dropped, so renamed-away paths
don't crowd out live ones.

Prints the --top pairs seen at least --min times, most frequent first, one per line:

    <together>  <share>%  <file a>  <file b>

where <share> is <together> over the commit count of the file that changed less, so
100% means it never changed without the other. Pairs in different modules at a high
share are hidden links; a pair in one module is expected.

Exits 0 (also when nothing qualifies, or the repo has no commits yet), 2 on bad usage,
outside a git repo, or when git log fails. Stdlib only.
"""

import argparse
import itertools
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

SINCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 .:,_+-]*")


class GitError(Exception):
    pass


def commits(since):
    """Each non-merge commit's changed files, repo-root relative, unquoted."""
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "log", "--no-merges", "--since", since,
         "--name-only", "--format=%x00"],
        capture_output=True, text=True, check=False)
    if result.returncode:
        raise GitError(result.stderr.strip())
    for block in result.stdout.split("\0"):
        files = sorted({line for line in block.splitlines() if line})
        if files:
            yield files


def in_scope(path, scopes):
    return not scopes or any(s == "" or path == s or path.startswith(s + "/") for s in scopes)


def main(argv):
    parser = argparse.ArgumentParser(prog="co-change.py", description="List file pairs that change together.")
    parser.add_argument("--since", default="6.months", help="how far back to look (default 6.months)")
    parser.add_argument("--top", type=int, default=30, help="pairs to print (default 30)")
    parser.add_argument("--min", type=int, default=3, help="minimum commits together (default 3)")
    parser.add_argument("--max-files", type=int, default=30, help="skip commits touching more files (default 30)")
    parser.add_argument("paths", nargs="*", help="only count files under these paths")
    args = parser.parse_args(argv)

    if not SINCE.fullmatch(args.since):
        parser.error(f"--since: not a date or relative time: {args.since!r}")
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    if top.returncode:
        print("co-change.py: not inside a git repository", file=sys.stderr)
        return 2
    root = Path(top.stdout.strip()).resolve()
    head = subprocess.run(["git", "rev-parse", "--verify", "--quiet", "HEAD"], capture_output=True, check=False)
    if head.returncode:
        return 0

    scopes = set()
    for path in args.paths:
        scope = Path(os.path.realpath(path))
        if not scope.is_relative_to(root):
            parser.error(f"path outside the repository: {path}")
        rel = scope.relative_to(root).as_posix()
        scopes.add("" if rel == "." else rel)

    per_file, pairs = Counter(), Counter()
    try:
        for files in commits(args.since):
            if len(files) > args.max_files:
                continue
            files = [f for f in files if in_scope(f, scopes)]
            per_file.update(files)
            pairs.update(itertools.combinations(files, 2))
    except GitError as err:
        print(f"co-change.py: git log failed: {err}", file=sys.stderr)
        return 2

    rows = [(n, a, b) for (a, b), n in pairs.items()
            if n >= args.min and (root / a).exists() and (root / b).exists()]
    rows.sort(key=lambda r: (-r[0], r[1], r[2]))
    for n, a, b in rows[:args.top]:
        share = round(100 * n / min(per_file[a], per_file[b]))
        print(f"{n}\t{share}%\t{a}\t{b}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
