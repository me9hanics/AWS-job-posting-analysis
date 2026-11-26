# B27 — Move merge and history rebuild

Status: done · Milestone: M5 Data layer · Phase 5 · Size: M

- Depends on: B26, B04, B02a
- Files: `src/jobscraping/data/merge.py`,
  `src/jobscraping/pipelines/store_universal.py`

## Do

1. Move `merge_observations` and the history-rebuild logic.
2. Keep the B04 fixtures as the parity gate.
3. Make a second merge idempotent.
4. Move the `last_modified_on` computation from B02a here, unchanged in
   behaviour.

Applying the merge rule is deliberately **not** part of this move: B27 keeps
byte parity with the B04 fixtures, and B27a applies the general
non-empty-observation rule (including the description) with its own fixture
update.

## Done when

- `data/merge.py` imports no pipeline module.
- The B04 (and B02a) tests pass unchanged.
- Byte-identical JSON on a repeated fixture run.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)). History-only storage
  (Q32) stays a write-path change: the merge can write history alone.
