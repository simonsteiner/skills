#!/usr/bin/env python3
"""Fail on em and en dashes, which make prose read as machine-written; CI and lefthook run it.

    scripts/check-dashes.py              every tracked file
    scripts/check-dashes.py a.md b.py    just these (lefthook passes the staged files)

Prints `path:line:col: <dash>` for each one and exits 1, or prints "ok". Rewrite each with the
punctuation the sentence needs: commas or parentheses around an aside, a colon or semicolon
before an explanation, a hyphen in a range (1-5). Files that aren't UTF-8 text are skipped.
"""

import subprocess
import sys
from pathlib import Path

DASHES = {chr(0x2014): "em dash", chr(0x2013): "en dash"}


def problems(path):
    """`path:line:col: kind` for each dash in one file; none for a missing or non-text file."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return [f"{path}:{n}:{col}: {kind}"
            for n, line in enumerate(text.splitlines(), 1)
            for col, char in enumerate(line, 1)
            if (kind := DASHES.get(char))]


def main(argv):
    files = argv or subprocess.run(["git", "ls-files", "-z"], capture_output=True, text=True,
                                   check=True).stdout.split("\0")
    found = [p for f in files if f for p in problems(f)]
    print("\n".join(found) if found else "ok")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
