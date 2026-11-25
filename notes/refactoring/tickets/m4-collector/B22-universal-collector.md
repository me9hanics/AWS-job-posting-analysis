# B22 — Create the universal collector

Status: done · Milestone: M4 Collector · Phase 4 · Size: L

- Depends on: B09, B10, B19, B20, B21
- Files: `src/jobscraping/acquisition/collector.py`,
  `src/jobscraping/config/models.py`, `src/jobscraping/scrapers/steps.py`,
  `tests/test_collector.py` (new)

## Do

1. Implement `run_collection(adapters, config)`.
2. Iterate adapters and their declared steps in order (each adapter's
   `listings` step owns its query × location units in M4); honor
   `CollectionConfig.steps`; merge by identity.
3. Record step outcomes and errors in a run report structure.
4. Do not store files here; return records plus the report.

## Implementation notes

`CollectionConfig` becomes concrete here in `config/models.py` — B32 only adds
`ProfileConfig` to that module later. Its cache fields
(`cached_postings`, `cache_hit_predicate`) sit with `cache_mode` and are
excluded from `scope_digest()`; the digest covers `sites`, `queries`,
`locations`, `steps` and `overrides` only. `CollectionConfigLike` in
`scrapers/steps.py` already carries the two cache fields (B19); its "lands with
B32" docstring is corrected here.

`adapters` are constructed instances, not classes: steps are bound methods and
the caller (the pipeline in B24, a test in B25) owns run context. The collector
therefore needs no constructor arguments and imports no site module.

Report rules: one entry per declared step, with `ok` / `skipped` / `failed` /
`empty`; an exception is recorded and later steps still run; an empty result
after any step is `empty` and fails that adapter; an overall empty record set
sets `zero_records` and fails the run. No spec checks (B37), no chunk reuse
(B38) and no file writes (B23).

Tests: create `tests/test_collector.py` with the B10 shapes promoted to the real
call (one-step, two-step, skip, raising step, zero records). B23 and B25 extend
the same module.

See [implementation-flow.md](implementation-flow.md#b22--the-universal-collector).

## Checks

Ruff and ty are clean on the new files. `scrapers/steps.py` carries one
pre-existing `I001` (import block order, line 10); this ticket only corrects its
docstring and leaves that finding untouched. `ty check src` reports the baseline
94 diagnostics, none of them from `config/models.py` or
`acquisition/collector.py`.

The collector's step catch is a broad `except Exception` because the collector
rules mandate it: one step failing must not stop later steps and must be
recorded. It carries no `noqa`; the current ruff default rule set reports
`BLE001` (blind except) on it, and that finding stays reported rather than
suppressed.

## Done when

- A one-step and a two-step adapter both run.
- Skipping a step is observable.
- Zero records is a failure.
- The collector imports no profile and no site module by name.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)). A "too many arguments"
  finding on `run_collection` is raised with the user, with variants.
