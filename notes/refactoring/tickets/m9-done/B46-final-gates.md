# B46 — Final gates

Status: todo · Milestone: M9 Done · Phase 9 · Size: S

- Depends on: B44, B45b
- Files: all

## Do

1. Run the full suite.
2. Run the import audit, duplicate-class audit, absolute-path audit and the
   trace audit: `rg -i dani src/jobscraping/{data,processing,pipelines,io}` must
   only match `profiles/`, `conf/` and tests (D26).
3. Run `uvx ruff check src tests` and `uvx ty check src` over the whole tree.
   Add the tools as a dev group or a config file only if the run needs it.
4. Build the docs with `uv run sphinx-build -b html docs docs/_build`.
5. Clone into a fresh directory and run the documented command and the docs
   build.

## Done when

- All tests pass.
- No absolute path in `src`/`tests`.
- One implementation per scraper class.
- No dead module/function/constant and no profile trace outside `profiles/` and
  `conf/`.
- `ruff` and `ty` report no finding anywhere in `src`/`tests`.
- The docs build without warnings.
- The fresh-clone run works without machine setup.

This is the definition of done for the refactoring round, not for every future
site or profile.
