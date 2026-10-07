# Changesets are applied on main directly, without a version PR

## Context

The changesets setup came over from `mattpocock/skills` with the fork. Every PR adds a `.changeset/*.md` note, and the `Release` workflow on `main` used `changesets/action` to open a "chore: version skills" PR that bumped `package.json` and wrote `CHANGELOG.md`, then tagged the release once that PR merged.

That PR never got opened. The repo doesn't allow GitHub Actions to create pull requests, so every `Release` run failed and fifteen changesets piled up. The version PR also gates nothing:

- Skills install with `npx skills add simonsteiner/skills`, which takes the default branch. It ignores `package.json`, tags, and releases.
- `package.json` is `private` and never published, and `.claude-plugin/plugin.json` has no version.
- [ADR 0002](./0002-curate-third-party-skills-instead-of-vendoring.md) already accepts that nothing is pinned.

The per-PR notes are still worth keeping. They make a readable changelog, and because each one is its own file, parallel and stacked PRs never conflict the way they would if every PR edited `CHANGELOG.md`.

## Decision

**Keep writing a changeset per PR, and have CI apply them straight to `main`.** On every push to `main` that has pending changesets, the `Changelog` workflow (`.github/workflows/changelog.yml`) runs `changeset version` and pushes a `chore: update changelog` commit to `main`. There is no version PR and no tag. The `package.json` version still goes up, but only so each changelog entry gets a heading.

The fifteen changesets that had piled up were applied locally as 1.1.0.

## Consequences

- **No repo setting to loosen.** Pushing to `main` needs only `contents: write`, and `main` has no branch protection. If protection is ever added, this push breaks: allow the Actions bot through, or move to a GitHub App token.
- **`main` gets bot commits.** One follows every merge that carried a changeset. A push made with `GITHUB_TOKEN` doesn't trigger workflows, so the commit doesn't re-run the workflow or `lint.yml`.
- **The version number means "how much has changed", not "what to install".** If something ever needs to pin or roll back, that's ADR 0002's trigger for a real registry.
