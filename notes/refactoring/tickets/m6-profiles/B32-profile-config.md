# B32 — Add `ProfileConfig`

Status: todo · Milestone: M6 Profiles · Phase 6 · Size: M

- Depends on: B07
- Files: `src/jobscraping/config/models.py`, `src/jobscraping/profiles/dani.py`

## Do

1. Add the frozen `ProfileConfig` from [design/specs.md](../../design/specs.md).
   Add no input-source path: the caller passes records, never "the" universal
   history (Q28).
2. Move Dani threshold, salary, locations, scoring and language values into the
   Dani config/defaults.
3. Keep code behaviour unchanged.

## Done when

- `derive_profile_postings` can receive a `ProfileConfig`.
- Dani values are no longer scattered defaults in the pipeline signature.
- Tests pass.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
