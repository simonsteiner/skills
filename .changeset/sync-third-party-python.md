---
"simonsteiner-skills": minor
---

`scripts/sync-third-party.sh` is now `scripts/sync-third-party.py`, with the same `--check` and `--list` modes. A source that fails to install no longer stops the sync: the other sources still install, the universal-agent links are still made, and the failures are listed at the end. `--check` now also exits 1 when a retired skill is still installed or an agent's copy is out of date, not just when a curated skill is missing or comes from the wrong repo; uncurated and unmanaged installs are still only reported. The Python tooling is linted with ruff (`uvx ruff check scripts`), which needs [uv](https://docs.astral.sh/uv/).
