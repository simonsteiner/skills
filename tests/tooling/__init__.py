"""Tests for the repo tooling: the `tooling` package under scripts/.

The commands in scripts/ import it as `tooling` because Python puts a script's own
folder on the path; the tests get the same import by adding that folder here.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
