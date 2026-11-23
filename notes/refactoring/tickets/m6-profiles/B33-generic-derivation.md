# B33 — Make derivation generic

Status: todo · Milestone: M6 Profiles · Phase 6 · Size: L

- Depends on: B27, B28, B32
- Files: `src/jobscraping/processing/derive.py`,
  `src/jobscraping/processing/derive_profile_postings.py`

## Do

1. Move the generic derivation body into `processing/derive.py`. It takes its
   input records as an argument; no universal file, loader or history is
   assumed (Q28).
2. Accept `ProfileConfig` plus profile functions; remove Dani imports and
   defaults.
3. Keep the existing delta rules and output ordering.

## Done when

- `processing/derive.py` imports no profile module and loads no input file.
- Dani's selected output matches the baseline.
- A second config can call the same function.
