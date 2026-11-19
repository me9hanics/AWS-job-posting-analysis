# B35 — Make profile current selected-only

Status: todo · Milestone: M6 Profiles · Phase 6 · Size: S

- Depends on: B33, B34
- Files: `processing/derive.py`, tests

## Do

1. `current_postings.json` contains selected postings.
2. `newly_added_postings.json` keeps the agreed delta semantics.
3. Keep candidates in history.

## Done when

- A below-threshold candidate exists in history but not in current.
- A known reappearance is not newly added.
- The Dani test baseline is updated deliberately, not incidentally.
