#!/usr/bin/env python3
"""Read the git history for where tests lag the code, and where they move with it for no reason.

    test-history.py drift     [--since 6.months] [--top 30] [--min 3] [options] [<path>...]
    test-history.py fixes     [--since 6.months] [--top 30] [options] [<path>...]
    test-history.py refactors [--since 6.months] [--top 30] [--min 2] [options] [<path>...]
    test-history.py --help

Run inside a git repo. Walks the non-merge commits since --since (a date or a relative
time such as `6.months` or `2026-01-01`) on the current branch. A commit touching more
than --max-files files in the whole repo (a rename sweep, a formatter run) is skipped.
With paths (relative to the current directory), only source files under them count;
tests count wherever they live.

A path is a test when a folder in it is named test, tests, __tests__, spec, specs or
e2e, or its name looks like one (test_x.py, x_test.go, x.test.ts, x.spec.js, XTest.java,
XTests.cs, x_spec.rb, conftest.py), or it matches a --test-pattern regex. A source file
is any other file with a code extension. A source file's own tests are the tests at HEAD
whose name, minus the test affixes, equals its name (for index, __init__, mod, main and
lib: its folder's name). The pairing is a heuristic: check it before you cite it.

drift — the most-changed source files at HEAD, one per line:

    <commits>  <own>%  <any>%  <source>  <own tests, comma-separated, or ->

<own> is the share of those commits that also changed one of its own tests (- when it
has none), <any> the share that changed any test. A hot file with no own test, or a low
<own>, is behaviour that changes while nothing checks it.

fixes — fix commits (subject `fix:`/`fix(scope):`, or containing fix, fixes, fixed,
bug or hotfix) that changed a source file and no test, newest first:

    <sha>  <date>  <subject>  <source files, comma-separated>

then `# <n> of <m> fix commits changed no test`.

refactors — test files at HEAD changed by refactor commits (subject `refactor:`, or
containing refactor, rename, restructure or extract), which should leave behaviour and
so tests alone, most often first:

    <commits>  <test file>  <shas, comma-separated>

then `# <n> of <m> refactor commits changed a test`.

Exits 0 (also when nothing qualifies, or the repo has no commits yet), 2 on bad usage,
outside a git repo, or when git log fails. Stdlib only.
"""

import argparse
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

SINCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 .:,_+-]*")
CODE = {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".vue", ".svelte",
        ".go", ".rs", ".java", ".kt", ".kts", ".scala", ".groovy", ".rb", ".php", ".cs", ".fs",
        ".swift", ".m", ".c", ".h", ".cc", ".cpp", ".hpp", ".ex", ".exs", ".erl", ".clj",
        ".dart", ".lua", ".sh", ".bash", ".pl", ".r", ".jl", ".zig"}
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs", "e2e"}
TEST_NAME = re.compile(r"^test_.+\.py$|^conftest\.py$|_test\.\w+$|_spec\.rb$|\.(test|spec)\.\w+$"
                       r"|(Test|Tests|Spec|IT)\.(java|kt|scala|groovy|cs|fs|swift)$")
AFFIXES = re.compile(r"^test_|(_test|_spec|\.test|\.spec|Tests?|Spec|IT)$")
FOLDER_STEMS = {"index", "__init__", "mod", "main", "lib"}
FIX = re.compile(r"^(fix|bugfix|hotfix)(\([^)]*\))?!?:|\b(fix|fixes|fixed|bug|hotfix)\b", re.IGNORECASE)
REFACTOR = re.compile(r"^refactor(\([^)]*\))?!?:|\b(refactor\w*|renam\w*|restructur\w*|extract\w*)\b",
                      re.IGNORECASE)


class GitError(Exception):
    pass


class Kinds:
    def __init__(self, patterns):
        self.patterns = [re.compile(p) for p in patterns]

    def is_test(self, path):
        p = PurePosixPath(path)
        return (any(part.lower() in TEST_DIRS for part in p.parts[:-1]) or bool(TEST_NAME.search(p.name))
                or any(r.search(path) for r in self.patterns))

    def is_source(self, path):
        return PurePosixPath(path).suffix.lower() in CODE and not self.is_test(path)


def stem(path, test):
    p = PurePosixPath(path)
    name = p.name[: -len(p.suffix)] if p.suffix else p.name
    if test:
        name = AFFIXES.sub("", name)
    elif name in FOLDER_STEMS and len(p.parts) > 1:
        name = p.parts[-2]
    return name.lower().replace("-", "_")


def commits(since):
    """(sha, date, subject, files) for each non-merge commit, files repo-root relative."""
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "log", "--no-merges", "--since", since,
         "--date=short", "--name-only", "--format=%x00%h%x09%ad%x09%s"],
        capture_output=True, text=True, check=False)
    if result.returncode:
        raise GitError(result.stderr.strip())
    for block in result.stdout.split("\0")[1:]:
        head, _, rest = block.partition("\n")
        sha, date, subject = (head.split("\t", 2) + ["", ""])[:3]
        yield sha, date, subject, sorted({line for line in rest.splitlines() if line})


def in_scope(path, scopes):
    return not scopes or any(s == "" or path == s or path.startswith(s + "/") for s in scopes)


def drift(history, kinds, scopes, root, args):
    tracked = subprocess.run(["git", "-c", "core.quotePath=false", "ls-files"], capture_output=True,
                             text=True, check=False, cwd=root).stdout.splitlines()
    own = defaultdict(list)
    for t in (f for f in tracked if kinds.is_test(f)):
        own[stem(t, True)].append(t)
    total, with_own, with_any = Counter(), Counter(), Counter()
    for _, _, _, files in history:
        tests = {f for f in files if kinds.is_test(f)}
        for f in files:
            if kinds.is_source(f) and in_scope(f, scopes):
                total[f] += 1
                with_any[f] += bool(tests)
                with_own[f] += bool(tests.intersection(own[stem(f, False)]))
    rows = sorted(((n, f) for f, n in total.items() if n >= args.min and (root / f).exists()),
                  key=lambda r: (-r[0], r[1]))
    for n, f in rows[:args.top]:
        mine = sorted(own[stem(f, False)])
        share = f"{round(100 * with_own[f] / n)}%" if mine else "-"
        print(f"{n}\t{share}\t{round(100 * with_any[f] / n)}%\t{f}\t{','.join(mine) or '-'}")


def fixes(history, kinds, scopes, args):
    fix_commits, untested = 0, []
    for sha, date, subject, files in history:
        sources = [f for f in files if kinds.is_source(f) and in_scope(f, scopes)]
        if not FIX.search(subject) or not sources:
            continue
        fix_commits += 1
        if not any(kinds.is_test(f) for f in files):
            untested.append((sha, date, subject, sources))
    for sha, date, subject, sources in untested[:args.top]:
        print(f"{sha}\t{date}\t{subject}\t{','.join(sources)}")
    print(f"# {len(untested)} of {fix_commits} fix commits changed no test")


def refactors(history, kinds, scopes, root, args):
    seen, touched, shas = 0, 0, defaultdict(list)
    for sha, _, subject, files in history:
        if not REFACTOR.search(subject) or not any(kinds.is_source(f) and in_scope(f, scopes) for f in files):
            continue
        seen += 1
        tests = [f for f in files if kinds.is_test(f)]
        touched += bool(tests)
        for t in tests:
            shas[t].append(sha)
    rows = sorted(((len(s), t) for t, s in shas.items() if len(s) >= args.min and (root / t).exists()),
                  key=lambda r: (-r[0], r[1]))
    for n, t in rows[:args.top]:
        print(f"{n}\t{t}\t{','.join(shas[t])}")
    print(f"# {touched} of {seen} refactor commits changed a test")


def main(argv):
    parser = argparse.ArgumentParser(prog="test-history.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=["drift", "fixes", "refactors"])
    parser.add_argument("--since", default="6.months", help="how far back to look (default 6.months)")
    parser.add_argument("--top", type=int, default=30, help="rows to print (default 30)")
    parser.add_argument("--min", type=int, help="drift: minimum commits (default 3); refactors: minimum (default 2)")
    parser.add_argument("--max-files", type=int, default=30, help="skip commits touching more files (default 30)")
    parser.add_argument("--test-pattern", action="append", default=[], metavar="REGEX",
                        help="also count paths matching REGEX as tests (repeatable)")
    parser.add_argument("paths", nargs="*", help="only count source files under these paths")
    args = parser.parse_args(argv)
    if args.min is None:
        args.min = 3 if args.mode == "drift" else 2

    if not SINCE.fullmatch(args.since):
        parser.error(f"--since: not a date or relative time: {args.since!r}")
    try:
        kinds = Kinds(args.test_pattern)
    except re.error as err:
        parser.error(f"--test-pattern: {err}")
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    if top.returncode:
        print("test-history.py: not inside a git repository", file=sys.stderr)
        return 2
    root = Path(top.stdout.strip()).resolve()
    scopes = set()
    for path in args.paths:
        scope = Path(os.path.realpath(path))
        if not scope.is_relative_to(root):
            parser.error(f"path outside the repository: {path}")
        rel = scope.relative_to(root).as_posix()
        scopes.add("" if rel == "." else rel)
    head = subprocess.run(["git", "rev-parse", "--verify", "--quiet", "HEAD"], capture_output=True, check=False)
    if head.returncode:
        return 0

    try:
        history = [c for c in commits(args.since) if len(c[3]) <= args.max_files]
    except GitError as err:
        print(f"test-history.py: git log failed: {err}", file=sys.stderr)
        return 2
    if args.mode == "drift":
        drift(history, kinds, scopes, root, args)
    elif args.mode == "fixes":
        fixes(history, kinds, scopes, args)
    else:
        refactors(history, kinds, scopes, root, args)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
