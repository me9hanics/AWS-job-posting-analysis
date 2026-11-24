# B07a — Put profile-neutral annotations in the universal spec

Status: done · Milestone: M2 Contracts · Phase 1 · Size: S

- Depends on: B07, B08
- Files: `src/jobscraping/specs/postings.py`, `tests/test_specs.py`

## Why

Q29 (2026-11-24): the universal record carries fields that are facts about the
posting, not profile choices. `matched_titlewords` already arrived with
`RAW_POSTING_FIELDS`, but `language` and `guessed_required_languages` were
declared only in `SCORED_POSTINGS`. See
[design/specs.md](../../design/specs.md#profile-neutral-annotations).

B07 is done and closed; this is the one completed ticket whose output changes,
so it is a follow-up rather than a reopened ticket.

## Do

1. Declare `language` and `guessed_required_languages` in
   `UNIVERSAL_POSTINGS`, `produced_by="enrichment"`; declare the latter as
   `dict`, matching `guess_required_languages`'s return value.
2. In `SCORED_POSTINGS`/`SELECTED_POSTINGS`, mark `language`,
   `matched_titlewords` and `guessed_required_languages` as carried
   (`produced_by` names the universal producer). Keep `points`, `keywords`,
   `role_families`, `language_adjustment`, `language_excluded` and
   `profile_excluded` as `produced_by="derivation"`.
3. Add a test in `tests/test_specs.py`: the three annotations are universal
   fields; no policy field (`points`, `keywords`, `role_families`,
   `language_adjustment`, `language_excluded`, `profile_excluded`) is.

## Done when

- `UNIVERSAL_POSTINGS` declares the three annotations and no policy field.
- The spec test fails if a policy field is added to universal.
- `guessed_required_languages` is declared `dict`, matching the
  `guess_required_languages` return; the old `list` declaration is corrected here
  because the field is re-declared for universal.
- No runtime behaviour changes: specs remain metadata; no producer exists yet.

## Implementation notes

Spec-only change. The producers land later: B29 fills the two language fields in
`data/enrich.py`, B31 stores them, B33 consumes instead of recomputing. Nothing
in this ticket should touch collection, derivation or `factual_postings`.

The milestone view is
[implementation-flow.md](implementation-flow.md#b07a--universal-annotations).
