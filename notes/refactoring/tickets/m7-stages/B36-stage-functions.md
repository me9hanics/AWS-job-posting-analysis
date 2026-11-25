# B36 — Extract stage functions

Status: todo · Milestone: M7 Stages · Phase 7 · Size: L

- Depends on: B24, B33
- Files: `src/jobscraping/pipelines/collection.py`, `derivation.py`, `outputs.py`

## Do

1. Give each stage a named input, named output and explicit config. Inputs are
   supplied by the pipeline; a stage does not discover or require a universal
   history (Q28).
2. Keep the existing composite functions as thin sequences during migration.
3. Remove file-format and profile details from pipeline modules.

## Done when

- Every stage can run on fixtures without network, including fixtures that are
  not a universal history.
- The old entry points call the same stages.
- No stage duplicates business logic.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
