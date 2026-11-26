# B28 — Make the diff neutral

Status: done · Milestone: M5 Data layer · Phase 5 · Size: S

- Depends on: B27
- Files: `src/jobscraping/data/compare.py`,
  `src/jobscraping/processing/postings_utils.py`,
  `src/jobscraping/processing/derive_profile_postings.py`

## Do

1. Move `get_added_and_removed` into `data/compare.py` as a pure diff over
   records; keep a path-tolerant wrapper of the same name in `postings_utils`
   for the legacy callers (Q16).
2. Remove the `points = 0` injection and the `points` ordering; profile
   derivation adds its own default and ordering so its output is unchanged.
3. Add tests for added, removed and reappeared identities.

## Done when

- A universal diff contains no profile policy field.
- A reappearing posting is current, not newly added.
- The profile path still orders by points after derivation.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)). The diff and the current
  view are computed from history, so neither file is the only carrier of a fact
  (Q32).
