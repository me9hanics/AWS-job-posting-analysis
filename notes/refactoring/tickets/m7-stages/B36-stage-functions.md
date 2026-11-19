# B36 — Extract stage functions

Status: todo · Milestone: M7 Stages · Phase 7 · Size: L

- Depends on: B24, B33
- Files: `src/jobscraping/pipelines/collection.py`, `derivation.py`, `outputs.py`

## Do

1. Give each stage a named input, named output and explicit config.
2. Keep the existing composite functions as thin sequences during migration.
3. Remove file-format and profile details from pipeline modules.

## Done when

- Every stage can run on fixtures without network.
- The old entry points call the same stages.
- No stage duplicates business logic.
