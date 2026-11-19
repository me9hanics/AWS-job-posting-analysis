# B28 — Make the diff neutral

Status: todo · Milestone: M5 Data layer · Phase 5 · Size: S

- Depends on: B27
- Files: `src/jobscraping/data/compare.py`,
  `src/jobscraping/processing/postings_utils.py`

## Do

1. Move `get_added_and_removed` into `data/compare.py`.
2. Remove the `points = 0` injection; profile derivation adds its own default.
3. Add tests for added, removed and reappeared identities.

## Done when

- A universal diff contains no profile field.
- A reappearing posting is current, not newly added.
- The profile path still orders by points after derivation.
