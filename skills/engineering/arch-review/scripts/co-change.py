#!/usr/bin/env python3
"""List the pairs of files that keep changing in the same commit, or the files that change most.

    co-change.py [--churn] [--since 6.months] [--top 30] [--min 3] [--max-files 30]
                 [--exclude <glob>]... [--no-default-excludes] [<path>...]
    co-change.py --help

Run inside a git repo. Walks the commits since --since (a date or a relative time
such as `6.months` or `2026-01-01`) on the current branch, skipping merges, and counts
every pair of files changed together. A commit touching more than --max-files files in
the whole repo (a rename sweep, a formatter run) says nothing about coupling and is
skipped, whatever the paths. With paths (relative to the current directory), only
files under them count. Files that no longer exist are dropped, so renamed-away paths
don't crowd out live ones.

Files that change with everything say nothing about design, so these never count:
lockfiles (package-lock.json, yarn.lock, uv.lock, Cargo.lock, go.sum, ...), changelogs
(CHANGELOG*), and paths .gitattributes marks `linguist-generated`. --no-default-excludes
counts them again. Each --exclude <glob> drops more: it's matched with fnmatch against the
repo-relative path and against the file name, so `*.snap` and `docs/*` both work. An
excluded file still counts toward --max-files.

Prints the --top pairs seen at least --min times, most frequent first, one per line:

    <together>  <share>%  <file a>  <file b>

where <share> is <together> over the commit count of the file that changed less, so
100% means it never changed without the other. Pairs in different modules at a high
share are hidden links; a pair in one module is expected.

--churn prints the hot spots instead: the --top files changed in at least --min of
those commits, most first, one per line:

    <commits>  <file>

It counts the same commits and files as the pairs, so the excludes, paths and
--max-files apply to it too.

Exits 0 (also when nothing qualifies, or the repo has no commits yet), 2 on bad usage,
outside a git repo, or when git fails. Stdlib only.
"""

import argparse
import fnmatch
import itertools
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

SINCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 .:,_+-]*")

# File names that change with every dependency bump or release, whatever the design.
DEFAULT_EXCLUDES = (
    "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock",
    "bun.lockb", "deno.lock", "Cargo.lock", "go.sum", "uv.lock", "poetry.lock", "Pipfile.lock",
    "pdm.lock", "composer.lock", "Gemfile.lock", "mix.lock", "pubspec.lock", "Podfile.lock",
    "Package.resolved", "packages.lock.json", "gradle.lockfile", "flake.lock", "CHANGELOG*",
)


class GitError(Exception):
    pass


def commits(since):
    """Each non-merge commit's changed files, repo-root relative, unquoted."""
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "log", "--no-merges", f"--since={since}",
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


def matches(path, globs):
    name = path.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatchcase(path, g) or fnmatch.fnmatchcase(name, g) for g in globs)


def generated(paths, root):
    """The paths whose linguist-generated attribute is set (from any .gitattributes)."""
    if not paths:
        return set()
    result = subprocess.run(
        ["git", "check-attr", "-z", "--stdin", "linguist-generated"], cwd=root,
        input="\0".join(paths) + "\0", capture_output=True, text=True, check=False)
    if result.returncode:
        raise GitError(result.stderr.strip())
    fields = result.stdout.split("\0")
    return {path for path, _, value in zip(fields[0::3], fields[1::3], fields[2::3])
            if value in ("set", "true")}


def main(argv):
    parser = argparse.ArgumentParser(prog="co-change.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--churn", action="store_true",
                        help="print the most-changed files instead of the pairs")
    parser.add_argument("--since", default="6.months", help="how far back to look (default 6.months)")
    parser.add_argument("--top", type=int, default=30, help="rows to print (default 30)")
    parser.add_argument("--min", type=int, default=3,
                        help="minimum commits together, or per file with --churn (default 3)")
    parser.add_argument("--max-files", type=int, default=30, help="skip commits touching more files (default 30)")
    parser.add_argument("--exclude", action="append", default=[], metavar="GLOB",
                        help="never count files matching GLOB (repeatable)")
    parser.add_argument("--no-default-excludes", action="store_true",
                        help="count lockfiles, changelogs and linguist-generated files too")
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

    globs = list(args.exclude) if args.no_default_excludes else [*DEFAULT_EXCLUDES, *args.exclude]
    try:
        kept = [[f for f in files if in_scope(f, scopes) and not matches(f, globs)]
                for files in commits(args.since) if len(files) <= args.max_files]
        dropped = set() if args.no_default_excludes else generated(sorted({f for fs in kept for f in fs}), root)
    except GitError as err:
        print(f"co-change.py: git failed: {err}", file=sys.stderr)
        return 2

    per_file, pairs = Counter(), Counter()
    for files in kept:
        files = [f for f in files if f not in dropped]
        per_file.update(files)
        pairs.update(itertools.combinations(files, 2))

    if args.churn:
        hot = [(n, f) for f, n in per_file.items() if n >= args.min and (root / f).exists()]
        hot.sort(key=lambda r: (-r[0], r[1]))
        for n, f in hot[:args.top]:
            print(f"{n}\t{f}")
        return 0

    rows = [(n, a, b) for (a, b), n in pairs.items()
            if n >= args.min and (root / a).exists() and (root / b).exists()]
    rows.sort(key=lambda r: (-r[0], r[1], r[2]))
    for n, a, b in rows[:args.top]:
        share = round(100 * n / min(per_file[a], per_file[b]))
        print(f"{n}\t{share}%\t{a}\t{b}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
