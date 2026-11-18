#!/usr/bin/env python3
"""List the pairs of files that keep changing in the same commit.

    co-change.py [--since 6.months] [--top 30] [--min 3] [--max-files 30] [<path>...]
    co-change.py --help

Run inside a git repo. Walks the commits since --since (anything `git log --since`
takes) on the current branch, skipping merges, and counts every pair of files changed
together. A commit touching more than --max-files files (a rename sweep, a formatter
run) says nothing about coupling and is skipped. With paths, only files under them
count. Files that no longer exist are dropped, so renamed-away paths don't crowd out
live ones.

Prints the --top pairs seen at least --min times, most frequent first, one per line:

    <together>  <share>%  <file a>  <file b>

where <share> is <together> over the commit count of the file that changed less, so
100% means it never changed without the other. Pairs in different modules at a high
share are hidden links; a pair in one module is expected.

Exits 0 (also when nothing qualifies), 2 on bad usage or outside a git repo. Stdlib only.
"""

import argparse
import itertools
import subprocess
import sys
from collections import Counter
from pathlib import Path


def commits(since, paths):
    out = subprocess.run(
        ["git", "log", "--no-merges", f"--since={since}", "--name-only", "--format=%x00", "--", *paths],
        capture_output=True, text=True, check=True).stdout
    for block in out.split("\0"):
        files = sorted({line for line in block.splitlines() if line})
        if files:
            yield files


def main(argv):
    parser = argparse.ArgumentParser(prog="co-change.py", description="List file pairs that change together.")
    parser.add_argument("--since", default="6.months", help="how far back to look (default 6.months)")
    parser.add_argument("--top", type=int, default=30, help="pairs to print (default 30)")
    parser.add_argument("--min", type=int, default=3, help="minimum commits together (default 3)")
    parser.add_argument("--max-files", type=int, default=30, help="skip commits touching more files (default 30)")
    parser.add_argument("paths", nargs="*", help="only count files under these paths")
    args = parser.parse_args(argv)

    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    if top.returncode:
        print("co-change.py: not inside a git repository", file=sys.stderr)
        return 2
    root = Path(top.stdout.strip())

    per_file, pairs = Counter(), Counter()
    for files in commits(args.since, args.paths):
        if len(files) > args.max_files:
            continue
        per_file.update(files)
        pairs.update(itertools.combinations(files, 2))

    rows = [(n, a, b) for (a, b), n in pairs.items()
            if n >= args.min and (root / a).exists() and (root / b).exists()]
    rows.sort(key=lambda r: (-r[0], r[1], r[2]))
    for n, a, b in rows[:args.top]:
        share = round(100 * n / min(per_file[a], per_file[b]))
        print(f"{n}\t{share}%\t{a}\t{b}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
