# B21 — Extract the quality gate

Status: todo · Milestone: M4 Collector · Phase 4 · Size: S

- Depends on: B15
- Files: `src/jobscraping/acquisition/quality.py`,
  `src/jobscraping/pipelines/collecting.py`

## Do

1. Move `validate_postings_quality` and its helpers into `acquisition/`.
2. Keep a re-export in `collecting.py` until its callers move.
3. Add tests for pass/fail cases with per-source thresholds.

## Done when

- The quality gate imports no profile module.
- Existing tests pass.
- `collecting.py` is thinner by the moved functions.
