# B04 — Characterization tests for data rules

Status: done · Milestone: M1 Safe baseline · Phase 0 · Size: M

- Depends on: B02
- Files: `tests/test_data_rules.py` (new), `tests/fixtures/`

## Do

1. Lock current behaviour for `factual_postings`: profile keys are dropped, raw
   keys survive, and unknown keys are dropped.
2. Lock `merge_observations`: earliest `first_collected_on`, latest
   `last_collected_on`, recomputed `timespan_days`, and the latest description
   winning even when it is empty (there is no non-empty guard today; B27 owns
   that rule), plus an idempotent second merge.
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
  test pins that current behaviour; B27 owns the intended non-empty rule.
- Added/removed order is deterministic only when `points` differ. Ties follow the
  iteration order of a set difference, so the tests assert set membership there.
  The ordering test does not assert the injected `points` values; B28 removes
  that side effect.
- Broken-merge check (both mutations reverted): swapping `min`/`max` in
  `merge_observations` failed 9 tests, including both date-range tests and the
  `last_modified_on` cases; reversing the merge precedence (`{**posting, **old}`
  instead of `{**old, **posting}`) failed 4 tests: the two description tests,
  the matched-titlewords union and the expected-history fixture.
- The fake-HTTP layers in `test_data_rules.py` and `test_scraper_fixtures.py`
  are deliberately separate: the former stubs
  `requests_responses_with_cookies`, the latter replaces `requests.Session`.
  They exercise different transport seams and are not the same helper.
