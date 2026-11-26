# B30 — Atomic writes, UTC and `schema_version`

Status: done · Milestone: M5 Data layer · Phase 5 · Size: M

- Depends on: B26
- Files: `src/jobscraping/io/files_io.py`, `src/jobscraping/data/load.py`,
  `src/jobscraping/config/constants.py`

## Do

1. Write to a temporary file in the destination directory and `os.replace`.
2. Use UTC for new artifact timestamps and filenames.
3. Add `schema_version` to vault artifacts as a per-folder `vault_meta.json`
   (`{schema_version, updated_at}`), written by `data/load.py`. Posting files
   keep their dict-keyed-by-identity shape, so a top-level key is not an option;
   `collection_scope.json` stays unchanged because its equality decides cache
   reuse.
4. Keep reading legacy local-time files without conversion.

## Done when

- A simulated write failure leaves the previous file intact.
- New timestamps are UTC.
- Every vault folder written by `data/load.py` has a `vault_meta.json` with
  `schema_version`.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).

## Note

Current artifacts are local-time; do not rewrite history in this ticket.
