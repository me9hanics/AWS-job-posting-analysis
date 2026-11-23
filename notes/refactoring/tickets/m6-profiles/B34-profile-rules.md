# B34 — Move profile rules and delete the empty modules

Status: todo · Milestone: M6 Profiles · Phase 6 · Size: M

- Depends on: B33
- Files: `src/jobscraping/profiles/dani.py`,
  `processing/candidate_filtering.py`, `selection_filtering.py`, `scoring.py`

## Do

1. Keep candidate admission, role contributions, language assessment and title
   exclusions in the profile module.
2. Put shared ranking/keyword mechanics in `processing/scoring_mechanics.py`.
3. Delete the three empty modules.

## Done when

- The empty modules are gone.
- `profiles/dani.py` imports no pipeline module.
- Candidate and selection behaviour are separately testable.
