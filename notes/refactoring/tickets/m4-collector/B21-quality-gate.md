# B21 — Extract the quality gate

Status: done · Milestone: M4 Collector · Phase 4 · Size: S

- Depends on: B15
- Files: `src/jobscraping/acquisition/quality.py`,
  `src/jobscraping/pipelines/collecting.py`

## Do

1. Move `validate_postings_quality` and its helpers into `acquisition/`.
2. Keep a re-export in `collecting.py` until its callers move.
3. Add tests for pass/fail cases with per-source thresholds.

## Implementation notes

The move creates the `acquisition` package (`__init__.py`). The function body
does not change; `collecting.py` imports and re-exports the name so
`get_postings`, `run_universal_scrape_flow` and the tests that patch it keep
working. The gate stays a pipeline call in M4 — the collector returns records and
a report and never raises the quality error itself (B22/B24).

New tests go in `tests/test_quality_gate.py` (pass and fail for a required field
and for a retention threshold on one source). The "no profile module" check is a
source scan, not a runtime assertion: `rg "profiles|profile"` over
`src/jobscraping/acquisition` → none.

See [implementation-flow.md](implementation-flow.md#b21--the-quality-gate-moves).

## Done when

- The quality gate imports no profile module.
- Existing tests pass.
- `collecting.py` is thinner by the moved functions.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
