# B04 — Characterization tests for data rules

Status: done · Milestone: M1 Safe baseline · Phase 0 · Size: M

- Depends on: B02
- Files: `tests/test_data_rules.py` (new), `tests/fixtures/`

## Do

1. Lock current behaviour for `factual_postings`: profile keys are dropped, raw
   keys survive, and unknown keys are dropped.
2. Lock `merge_observations`: earliest `first_collected_on`, latest
   `last_collected_on`, recomputed `timespan_days`, latest non-empty description,
   idempotent second merge.
3. Lock `get_added_and_removed` on identity sets and ordering; do not test the
   `points` side effect here, because B28 removes it.
4. Add a deliberately broken-merge check locally to prove the tests fail.

## Done when

- The new tests pass on unchanged code.
- A wrong date or description merge fails at least one test.

## Notes

These fixtures are also the parity gate for B27 and the baseline B02a extends.

## Implementation notes

- `factual_postings` keeps only `RAW_POSTING_FIELDS`, so a truly unknown key is
  dropped. The original wording ("unknown keys survive") was wrong and is
  corrected above.
- `merge_observations` has no non-empty guard on `description`: a later
  observation with an empty description replaces a stored non-empty one. The B04
  test pins that current behaviour; B02a/B27 decide whether to change it.
- Added/removed order is deterministic only when `points` differ. Ties follow the
  iteration order of a set difference, so the tests assert set membership there.
