# Out of scope

This folder records decisions about what this repo will **not** build. Each file documents a feature, request, or direction that was deliberately ruled out, and *why* — so the same idea doesn't get re-proposed and re-debated from scratch.

It's the inverse of [`docs/adr/`](../docs/adr/): ADRs record what we decided to do; these record what we decided not to do.

## When to add one

Write one when you turn down a plausible feature or request and the reasoning is worth keeping — especially if:

- it's likely to be asked for again,
- the cost (maintenance, surface area, complexity) is the real reason, or
- the "no" is a judgment call rather than an obvious one.

## Format

One file per ruled-out idea, named for the idea (e.g. `verify-mode.md`). Keep it short:

- **Title** — the thing that's out of scope, stated plainly.
- **Why this is out of scope** — the reasoning and the cost being avoided.
- **Prior requests** — links to issues/discussions where it came up, if any.
