# <Project name>

<What the project is, in one sentence.> <The major pieces.> <How they talk to each other.>
Domain terms are in `GLOSSARY.md`; decisions and their trade-offs are in `docs/adr/`.

## Commands

```bash
<install command>  # install dependencies
<dev command>  # start the dev server
<test command>  # run all tests
<single test command> path/to/file.test.ts  # run one test file
<lint command>  # lint and type-check
```

## Conventions

### <Area>

- **<X lives only in Y>.** <Never re-implement it; one sentence on what to use instead.>
- **<We use X, not Y>.** <One sentence.>

## Hard constraints

- **Never <action>.** <One sentence on what to do instead.>
- **Ask before <action>.** <One sentence.>

## Gotchas

- **<What trips people up>.** <One or two sentences.>

## Docs

- `README.md` — what the project is and the quickstart.
- `docs/setup.md` — local setup and troubleshooting.
- `.env.example` — every env var, annotated.
