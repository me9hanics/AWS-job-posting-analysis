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
4. Keep language **evidence** extraction (`extract_language_requirements`,
   `guess_required_languages`) generic; the profile keeps only the policy that
   turns evidence into `language_adjustment` and `language_excluded` (Q29).

## Implementation notes

`assess_language(text, posting_language, policy)` receives the detected language
today. After B29/B33 that value comes from the input record, so the profile
function only needs the evidence and its policy values. Do not move
`language_requirements.py` into `profiles/`; it is profile-neutral.

## Done when

- The empty modules are gone.
- `profiles/dani.py` imports no pipeline module.
- Candidate and selection behaviour are separately testable.
- The profile module contains no language-evidence parsing; it consumes the
  language and requirements from the record.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
