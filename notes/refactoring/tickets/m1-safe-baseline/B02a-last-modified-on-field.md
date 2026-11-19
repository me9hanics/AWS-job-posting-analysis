# B02a — Add a real `last_modified_on` field

Status: todo · Milestone: M1 Safe baseline · Phase 0 · Size: M

- Depends on: B04
- Added: 2026-11-19. This task was missing from the backlog; it takes the next
  free ID slot (`B02a`) so no existing ID moves.
- Files: `src/jobscraping/processing/postings_utils.py`,
  `src/jobscraping/pipelines/store_universal.py`, `src/jobscraping/config/constants.py`,
  `tests/test_data_rules.py`, [design/artifacts.md](../../design/artifacts.md)

## Problem

The vault has *collection* dates (`collected_on` per observation,
`first_collected_on`, `last_collected_on`, `timespan_days`) and the site's own
`date`. None of them says when the material last actually changed. Today a
posting observed ten times with identical content and one whose description was
edited are indistinguishable: `last_collected_on` moves for both.

## Do

1. Add one derived field, `last_modified_on` (`YYYY-MM-DD`), defined as the
   observation date on which any persisted fact of the posting last changed.
   Re-observing an unchanged posting does not move it.
2. Define "changed" explicitly in `design/artifacts.md` before coding. Proposed:
   compare each observation against the stored record, ignoring
   `CACHE_ALWAYS_FRESH_FIELDS` (`collected_on`, `date` in the cache sense,
   `isActive`, `url`) plus `last_modified_on` itself and merge bookkeeping
   (`first_collected_on`, `last_collected_on`, `timespan_days`). Decide whether
   `isActive` and `date` are site-refreshed noise or real changes; record the
   answer.
3. Set it on first observation to that observation's `collected_on`, so every
   record has a value and the field is never `None`.
4. Compute it in exactly one place: the merge (`merge_observations` now, the
   `data/merge.py` function after B27). Do not compute it in adapters, enrichment
   or derivation.
5. Add it to `RAW_POSTING_FIELDS` so it survives projection into the universal
   record, and to `UNIVERSAL_POSTINGS` in B07.
6. Decide output: add one `EXCEL_COLUMNS` entry and one `COLUMN_ORDER` position.
   The field is factual, so it may appear in universal records; it must never be
   derived from profile data.
7. Extend B04's merge fixtures with the four cases below.

## Acceptance cases

- First observation: `last_modified_on == collected_on`.
- Second observation with identical facts: `last_modified_on` unchanged,
  `last_collected_on` advanced.
- Second observation with a changed description: `last_modified_on` becomes the
  second observation's date.
- Merge is idempotent: a repeated merge does not move `last_modified_on`.

## Done when

- The four acceptance cases pass on the merge function.
- Every new universal record carries `last_modified_on`, and no adapter sets it.
- Removing the field from the merge fails at least one test.
- `design/artifacts.md` documents the field and the "changed" definition.

## Deliberately out of scope

- Backfilling `last_modified_on` for existing history. Existing files simply lack
  the field until their next observation; no old-data compatibility is required
  (Q27).
- Using the field for ordering, filtering or scoring.
