#!/usr/bin/env python3
"""Fail a commit when a staged, agent-authored file contains an em or en dash.

    check-dashes.py <path>...
    check-dashes.py --help

Meant for a lefthook pre-commit job, given {staged_files}. Em and en dashes are the
punctuation that most marks prose as machine-written, and agents reach for them by habit.
Reads the staged blob (what will be committed, not the working tree); a path the index
doesn't have is ignored. Skipped, because no agent writes them by hand:

- lockfiles, minified bundles, source maps and test snapshots
- tabular and geographic data (*.csv, *.tsv, *.geojson, *.jsonl, ...)
- anything under a vendor/, third_party/, node_modules/ or bower_components/ folder
- binary files: a NUL byte in the first 8000 bytes, or bytes that aren't UTF-8
- files git attributes mark linguist-generated or linguist-vendored (.gitattributes)
- files whose first lines carry a codegen header ("@generated", "DO NOT EDIT", ...)

The exemptions are check-file-tokens.py's, loaded from beside this script; both ship
together, in the skill's scripts/ and in the lefthook remote.
Prints `path:line:col: em dash` for each one, then how to rewrite them, on stderr.
Exits 0 when no file has one, 1 when any does, 2 on bad usage. Stdlib only.
"""

import argparse
import importlib.util
import os
import sys
from pathlib import Path

# Built from code points so this file passes its own check.
DASHES = {chr(0x2014): "em dash", chr(0x2013): "en dash"}


def _sibling(name):
    """Load a script beside this one as a module; its name has a hyphen, so no plain import.
    No bytecode is written: a __pycache__ would land in the skill or the remote's clone."""
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), Path(__file__).with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# What counts as a file no agent writes, and how to read the index, live in one place.
tokens = _sibling("check-file-tokens")

ADVICE = """\
Em and en dashes read as machine-written. Rewrite each with the punctuation the
sentence needs, without changing what it says:

- a pair around an aside: commas, or parentheses
- before an explanation, a consequence or a list: a colon, a semicolon, or a new sentence
- in a range (1-5, Mon-Fri): a hyphen
- a lone dash meaning "none" in a table: "-" or "none"
- in code that must produce one: an escape (\\u2014) rather than the literal character

A file that must hold them (translations, typography tests) goes in the job's
`exclude:` in lefthook.yml. Don't skip the hook with --no-verify."""


def dashes(path, blob):
    """`path:line:col: kind` for each dash in a UTF-8 blob; none for one that isn't UTF-8."""
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError:
        return []
    return [f"{path}:{n}:{col}: {kind}"
            for n, line in enumerate(text.splitlines(), 1)
            for col, char in enumerate(line, 1)
            if (kind := DASHES.get(char))]


def main(argv):
    parser = argparse.ArgumentParser(
        prog=os.path.basename(sys.argv[0]),
        description="Fail when a staged, agent-authored file contains an em or en dash.",
        epilog="Lockfiles, build output, binaries and generated files are skipped; see the script's docstring.")
    parser.add_argument("paths", nargs="*", help="files to check, normally lefthook's {staged_files}")
    args = parser.parse_args(argv)

    attributed = tokens.marked_by_attributes(args.paths)
    found = []
    for path in args.paths:
        blob = None if path in attributed else tokens.staged_blob(path)
        if blob is not None and not tokens.skip_reason(path, blob):
            found += dashes(path, blob)

    if found:
        print("\n".join(found) + "\n\n" + ADVICE, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
