"""The test suite: tests/tooling/ and tests/skill_scripts/.

A git hook that runs the suite (lefthook's pre-commit) exports GIT_DIR, GIT_INDEX_FILE
and friends. Every git call a test or the code under test makes would inherit them and
act on the repo being committed instead of its throwaway fixture: it once pushed junk
commits to a PR and set core.bare on the real repo. Dropping them here, before any test
module loads, covers subprocesses in tooling code too, not just the tests' own helpers.
"""

import os

for _name in [n for n in os.environ if n.startswith("GIT_")]:
    del os.environ[_name]
