# Profiles workstream

Status: decided direction 2026-11-16. Dani is partially migrated; the policy
seam is not generic.

Owns everything that answers "does this posting matter to this profile, how much,
and should it appear in the output". It must not own scraping, storage format or
generic facts.

## Current state

- `profiles/dani.py` (489 lines) holds constants and policy functions:
  `DANI_PHRASES`, `DANI_KEYWORD_SCORING`, `DANI_SALARY_BEARABLE`,
  `is_candidate`, `role_contributions`, `assess_language`, `title_excluded`.
- `processing/derive_profile_postings.py` defaults its keyword, ranking and
  salary arguments to Dani values and calls Dani functions directly, so the
  derivation module is still Dani-specific.
- `processing/candidate_filtering.py`, `selection_filtering.py` and `scoring.py`
  are empty; their intended ownership is documented in
  [the pipeline discussion](../../../src/jobscraping/processing/README.md).
- Shared profile-adjacent defaults live in `config/configs.py`: `BASE_PHRASES`,
  `BASE_KEYWORD_SCORING`, `BASE_TITLE_SCORING`, `BASE_COMPANY_SCORING`,
  `SALARY_BEARABLE`, `LOCATIONS_DESIRED`, `DEDUCT_COMPANIES`.
- `tech`, `legal` and `tn` still hold their constants and transformation lists
  inside `schedule/*_collect.py` and run through the legacy pipeline.
- Language policy is profile policy (`assess_language`), while posting language
  detection is generic (`analyze_text_language`). The split exists but is not
  enforced by module boundaries.
- `LanguageEvidence` in `processing/language_requirements.py` is a frozen
  dataclass; `profiles/dani.py` already imports `asdict`.

## Target

One `ProfileConfig` from `conf/`, plain profile functions, one generic
derivation path.

```text
config/
  models.py     # ProfileConfig: threshold, salary, locations, scoring values,
                # language values, output options (YAML-backed)
profiles/
  dani.py       # policy functions, no pipeline code
  tech.py       # added when tech is migrated
  ...
processing/
  derive.py             # generic: candidates -> history -> scores -> selection
  scoring_mechanics.py  # shared ranking/keyword mechanics
```

A profile module provides callables (candidate rule, role contributions,
language assessment, exclusions). `ProfileConfig` provides the tunable values.
The derivation module must not import a profile module; the caller supplies
config plus functions. There is no `ProfilePolicy` wrapper (Q5).

Scoring values and language values are not separate dataclasses: they are fields
of `ProfileConfig`. Scoring stays values plus shared mechanics, not a class (Q4).
A profile's `current_postings.json` holds selected postings only (Q19).

Profile modules stay Python. Configuration that a user may tune without a code
change moves to `conf/` when Kedro lands; behaviour (scoring rules with
functions) stays in code. See
[kedro-project.md](../design/kedro-project.md#parameters-vs-code).

## Changes

1. Define the profile contract: what `ProfileConfig` supplies and what callables
   a profile module supplies. No wrapper object. See
   [specs.md](../design/specs.md).
2. Make `derive_profile_postings` accept config and callables instead of Dani
   defaults. Move Dani defaults into `profiles/dani.py`.
3. Delete `candidate_filtering.py`, `selection_filtering.py` and `scoring.py`.
   Candidate and selection rules live in the profile module; shared scoring
   mechanics live in `processing/scoring_mechanics.py`.
4. Move scoring and language values out of `config/configs.py` into
   `ProfileConfig` (YAML) once each profile owns its values; keep only genuinely
   shared defaults in code.
5. Keep the two filter concepts distinct in the code: candidate admission
   (broad) and selection (final). Preserve Dani's delta semantics: known
   reappearances and score-only changes stay out of newly added.
6. Declare the `SCORED_POSTINGS` and `SELECTED_POSTINGS` specs and check them at
   the derivation boundary. The scored spec is what "fill out the spec" means
   for scoring: start from the input records the caller supplies (in practice
   universal records) and add the declared derived fields.
7. When converting tech/legal/tn, move their constants and transformation lists
   into their profile modules unchanged, then verify parity.
8. Keep profile text/scoring constants under review by the existing tests
   (`tests/test_dani_profile.py`, `tests/test_language_requirements.py`).
9. Derivation takes its records as an argument. It does not load a universal
   history, import a universal loader, or assume one history exists; a profile
   filter cannot know or care whether the input came from universal, another
   pipeline or a fixture (Q28).

## Dependencies

- Data workstream: derivation receives input records and writes profile
  artifacts through the data layer. It does not read a universal file by name.
- Pipelines workstream: policy construction moves to pipeline/CLI boundary.
- Kedro: profile parameters (`conf/*/parameters_<profile>.yml`) after the policy
  contract exists.

## Completion check

- `processing/derive.py` (or its equivalent) imports no profile module.
- Adding a profile means adding one policy module plus one `ProfileConfig`
  entry — no change to derivation, storage or acquisition.
- Dani's selected output is unchanged against the agreed baseline, and
  `current_postings.json` contains selected postings only.
- Candidate admission and selection are separately testable.
- A test asserts that a universal record has no profile score before derivation.
- A scored record missing a required `SCORED_POSTINGS` field is rejected with
  the field named.
- The three empty modules are deleted, not left as placeholders.

## Decided points

- No `ProfilePolicy` wrapper; config plus plain functions (Q5).
- No scoring class; values in `ProfileConfig` (Q4).
- Thresholds and scoring values are `conf/` parameters (Q6).
- Empty filtering/scoring modules are deleted (Q15).

How a profile's language policy is expressed without making the generic language
module profile-aware is an implementation detail inside the profile module. The
only open design question is Q16, the compatibility layer. See
[open-questions.md](../design/open-questions.md#still-open).

## Design references

- [Specs and dataclasses](../design/specs.md)
- [Module seams](../design/module-seams.md)
- [Decisions](../design/open-questions.md)
