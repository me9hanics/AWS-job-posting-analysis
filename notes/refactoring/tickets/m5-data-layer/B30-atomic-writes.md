# B30 — Atomic writes, UTC and `schema_version`

Status: todo · Milestone: M5 Data layer · Phase 5 · Size: M

- Depends on: B26
- Files: `src/jobscraping/io/files_io.py`, `src/jobscraping/data/load.py`

## Do

1. Write to a temporary file in the destination directory and `os.replace`.
2. Use UTC for new artifact timestamps and filenames.
3. Add `schema_version` to vault artifacts.
4. Keep reading legacy local-time files without conversion.

## Done when

- A simulated write failure leaves the previous file intact.
- New timestamps are UTC.
- Every vault file has `schema_version`.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).

## Note

Current artifacts are local-time; do not rewrite history in this ticket.
