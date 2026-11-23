# B06 — Create the `specs` package

Status: done · Milestone: M2 Contracts · Phase 1 · Size: S

- Depends on: B02
- Files: `src/jobscraping/specs/__init__.py`, `src/jobscraping/specs/base.py`

## Do

1. Add frozen `FieldSpec` and `DataSpec` dataclasses from
   [design/specs.md](../../design/specs.md).
2. Implement `DataSpec.extend()` and `DataSpec.check(records)`.
3. `check` returns human-readable problems; it does not mutate or coerce.
4. Keep the package a leaf: stdlib only.

## Done when

- `from jobscraping.specs.base import DataSpec, FieldSpec` works.
- The package imports without `pipelines`, `scrapers` or `profiles`.
