# Commit examples and edge cases

Reference for the `conventional-commit` skill. Spec:
<https://www.conventionalcommits.org/en/v1.0.0/>

## The grammar (v1.0.0)

```
<type>[optional scope][optional !]: <description>

[optional body]

[optional footer(s)]
```

Normative rules worth remembering:

- Type and a `: ` (colon + space) are **required**; description follows.
- Scope, when present, is a noun in parentheses right after the type: `fix(parser):`.
- A commit MAY be marked breaking with a `!` before the `:` and/or a `BREAKING CHANGE:` footer. With `!` and no footer, the description doubles as the breaking-change description.
- The body begins one blank line after the description and is free-form.
- Footers begin one blank line after the body. Each footer is `token: value` or `token #value`. Use `-` in place of spaces in tokens (`Reviewed-by`), with the sole exception of `BREAKING CHANGE`.
- `BREAKING CHANGE` may also be written `BREAKING-CHANGE:` (treated identically).

## SemVer correlation

- `fix:` → PATCH
- `feat:` → MINOR
- `BREAKING CHANGE` / `!` → MAJOR (on any type)

## Worked examples

### Simple feature, no scope

```
feat: add read-only SQL console at /debug-sql
```

### Feature with scope

```
feat(auth): add Better Auth email/password login behind a session wall
```

### Fix with a "why" body

```
fix: gate walk override on title keywords, never speed alone

A fast walk without a multisport title keyword was being reclassified as Paragliding. Require a keyword match; speed only promotes when paired with a speed-gated keyword.
```

### Refactor (no behaviour change)

```
refactor: split queries.ts grab-bag into domain query modules

Move per-domain SQL into queries/{activities,wellness,load,...}. No behaviour change; callers updated to the new import paths.
```

### Bug fix that closes an issue

```
fix(api): handle 429 from intervals.icu with backoff

Retry with exponential backoff up to 3 attempts before surfacing a 502.

Fixes #234
```

### Breaking change via `!`

```
feat(api)!: remove deprecated /login endpoint
```

### Breaking change via footer (with migration path)

```
feat(api): redesign the sync payload structure

BREAKING CHANGE: /api/sync now returns { type, action, payload } instead of { event, data }. Update clients to read the nested shape before upgrading.
```

### Revert

```
revert: feat: add export feature

This reverts commit 1234567890abcdef.
```

### Multiple footers / trailers

```
fix(auth): resolve concurrent login race condition

Add a row-level lock so simultaneous logins for one user can't both create a session.

Fixes #567
Refs #432
Co-authored-by: Jane Doe <jane@example.com>
```

## Good vs bad descriptions

| ✅ good                           | ❌ bad                       | why                           |
|---------------------------------- | ---------------------------- | ----------------------------- |
| `add user profile page`           | `Added user profile page`    | past tense, capitalised.      |
| `fix memory leak in file upload`  | `Fix Memory Leak.`           | title case, trailing period   |
| `remove deprecated API endpoint`  | `lots of changes`            | vague                         |

Imperative, present tense; lowercase first letter; no trailing period.

## Splitting unrelated changes

If a diff mixes, say, a bug fix and an unrelated dependency bump, propose two
commits rather than one:

```
fix(views): correct same-day filter using date(start_date)
```

```
chore(deps): bump astro to 6.3.4
```
