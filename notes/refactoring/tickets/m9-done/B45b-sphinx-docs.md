# B45b — Sphinx documentation in `docs/`

Status: todo · Milestone: M9 Done · Phase 9 · Size: S

- Depends on: B45
- Files: `docs/`, `pyproject.toml`, `.gitignore`

## Do

1. Set up a minimal Sphinx project in `docs/` that reads Markdown: `conf.py`
   with `myst_parser`, a start page and one API page.
2. Document the entry points only — collection, storing, derivation, outputs —
   and how to run them. Scraping internals stay in the adapter modules. Link the
   ADR pages B45 writes through an `adr/index.md` so no document is orphaned.
3. Build with `uv run sphinx-build -b html docs docs/_build` and keep
   `docs/_build` out of version control.

## Implementation notes

`docs/` exists and holds only the ADR pages B45 writes, so this ticket adds a
small tree around them rather than migrating anything:

```text
docs/conf.py        # project metadata, myst_parser, autodoc, src/ on sys.path
docs/index.md       # what the project does, install, run, links
docs/stages.md      # collection -> storing -> derivation -> outputs
docs/api.md         # autofunction entries for the entry points
docs/adr/index.md   # toctree over the ADR pages B45 writes
```

Both new dependencies (`sphinx`, `myst-parser`) go in a dev group in
`pyproject.toml`; they are documentation-only and must not enter the runtime
dependencies. `docs/_build/` is added to `.gitignore`.

`.. autofunction::` is preferred over `automodule` for the API page: it pins the
handful of functions a reader needs and keeps scraping modules out of the docs
without writing exclude patterns. The entry points are those B36 and B42–B43
settle on, so this ticket runs after them by construction.

The build must be reproducible from a fresh clone: no notebook execution, no
network fetches, no generated content outside `docs/_build`.

See [backlog.md](../../backlog.md#b45b--sphinx-documentation-in-docs).

## Done when

- The Sphinx build succeeds with no warning about a missing page or target.
- The start page links every other page, and the API page lists the entry-point
  functions.
- A fresh clone can build the docs after the documented install.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
