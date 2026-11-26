# B26 — Create `data/load.py`

Status: done · Milestone: M5 Data layer · Phase 5 · Size: S

- Depends on: B03
- Files: `src/jobscraping/data/load.py`, `src/jobscraping/pipelines/store_universal.py`

## Do

1. Move `load_postings` and the persistence wrapper into `data/load.py`.
2. Keep `files_io` as the file-format layer; `data/load.py` owns paths and record
   loading.
3. Update callers to use the data function.

## Done when

- `store_universal.py` no longer defines `load_postings`.
- Tests pass.
- No absolute path is introduced.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
