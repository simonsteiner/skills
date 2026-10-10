# Commit examples and edge cases

Worked examples for the `conventional-commit` skill. Spec: <https://www.conventionalcommits.org/en/v1.0.0/>

## Contents

- Feature, with and without a scope
- Fix with a "why" body
- Refactor
- Fix that closes an issue
- Breaking change via `!`, and via footer
- Revert
- Several footers
- Good vs bad descriptions
- Splitting unrelated changes

## Feature, with and without a scope

```text
feat: add read-only SQL console at /debug-sql
```

```text
feat(auth): add Better Auth email/password login behind a session wall
```

## Fix with a "why" body

```text
fix: gate walk override on title keywords, never speed alone

a fast walk without a multisport title keyword was being reclassified as Paragliding. Require a keyword match; speed only promotes when paired with a speed-gated keyword
```

## Refactor

```text
refactor: split queries.ts grab-bag into domain query modules

move per-domain SQL into queries/{activities,wellness,load,...}. No behaviour change; callers updated to the new import paths
```

## Fix that closes an issue

```text
fix(api): handle 429 from intervals.icu with backoff

retry with exponential backoff up to 3 attempts before surfacing a 502

Fixes #234
```

## Breaking change via `!`

With `!` and no footer, the description doubles as the breaking-change description.

```text
feat(api)!: remove deprecated /login endpoint
```

## Breaking change via footer

`BREAKING-CHANGE:` is accepted as a synonym.

```text
feat(api): redesign the sync payload structure

BREAKING CHANGE: /api/sync now returns { type, action, payload } instead of { event, data }. Update clients to read the nested shape before upgrading
```

## Revert

```text
revert: feat: add export feature

This reverts commit 1234567890abcdef.
```

The body here is git's own revert line; keep it as git wrote it.

## Several footers

Issue refs first, then trailers, one per line:

```text
fix(auth): resolve concurrent login race condition

add a row-level lock so simultaneous logins for one user can't both create a session

Fixes #567
Refs #432
Co-authored-by: Jane Doe <jane@example.com>
```

## Good vs bad descriptions

| ✅ good                           | ❌ bad                       | why                          |
|---------------------------------- | ---------------------------- | ---------------------------- |
| `add user profile page`           | `Added user profile page`    | past tense, capitalised      |
| `fix memory leak in file upload`  | `Fix Memory Leak.`           | title case, trailing period  |
| `remove deprecated API endpoint`  | `lots of changes`            | vague                        |

## Splitting unrelated changes

A diff mixing a bug fix and an unrelated dependency bump is two commits, each staged by path — the fix first if the bump doesn't depend on it:

```text
fix(views): correct same-day filter using date(start_date)
```

```text
chore(deps): bump astro to 6.3.4
```
