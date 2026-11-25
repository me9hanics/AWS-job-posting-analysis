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
4. Consume `language` and `guessed_required_languages` from the input when
   present; compute them only when missing, so legacy history still derives
   (Q29).

## Implementation notes

Today `derive_profile_postings` calls `analyze_postings_language` and
`guess_required_languages` on every input, including `previous_history`. After
B29/B31 the input already carries both. Keep the recompute as a fallback for
records without the fields — it is what makes old histories and hand-built
fixtures still work — but do not overwrite a supplied annotation.

`keywords`, `role_families`, `points`, `language_adjustment`,
`language_excluded` and `profile_excluded` stay derivation output.

## Done when

- `processing/derive.py` imports no profile module and loads no input file.
- Dani's selected output matches the baseline.
- A second config can call the same function.
- An input with the annotations is not re-annotated; an input without them
  produces today's result.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
