# Data workstream

Status: decided direction 2026-11-16. The universal flow exists for Dani; the
data layer is not yet separated from pipelines and processing.

Owns the universal vault, merge and comparison rules, generic enrichment and
history semantics. It does not scrape and does not know profiles. The universal
vault stores every posting; filtering is profile work.

## Current state

- `pipelines/store_universal.py` holds `load_postings`, `merge_observations`,
  `store_universal_postings` and `save_incomplete_run` — pipeline and pure data
  logic in one module.
- `processing/postings_utils.py` (514 lines) mixes comparison, history
  unification, enrichment and an import of `BaseScraper`.
- `processing/attributes.py` holds generic detection (language, salary,
  keyword matching) next to scoring helpers.
- Merge rules exist and are tested only indirectly: earliest `first_collected_on`,
  latest `last_collected_on`, recomputed `timespan_days`, merged
  `matched_titlewords`, latest description.
- `get_added_and_removed` injects `points = 0` when missing, so a profile field
  leaks into a generic comparison.
- There is no declared data shape. Each stage reads whatever keys it expects and
  the merge fills whatever it finds. Unknown keys are currently preserved by
  dict merging, which is the behaviour to keep.
- `data/save/postings/universal/` holds history files from earlier runs; their
  coverage differs from any single profile's query scope.

## Target

A small data layer with pure functions:

```text
data/
  load.py       # paths, JSON load/save, atomic write
  merge.py      # merge_observations, history rebuild, ID handling
  compare.py    # added/removed/diff without profile fields
  enrich.py     # rerunnable generic enrichment (salary, language, facts)
```

Every function takes records and returns records. Persistence is a thin wrapper.
A stage can therefore run on fixtures, on saved artifacts, or from a pipeline
node without changing behaviour.

The universal record shape is declared once in `specs/postings.py`
(`UNIVERSAL_POSTINGS`) and checked when data enters or leaves the layer. The
spec covers the fields processing relies on; extra keys are allowed and
preserved. See [specs.md](../design/specs.md).

Enrichment is idempotent and derived: rerunning it replaces derived values, it
does not append. Writes are atomic (temporary file plus `os.replace`), timestamps
are UTC, and vault artifacts carry a `schema_version`. No path in this layer is
absolute; the root is derived from `__file__`.

## Changes

1. Extract the pure functions from `store_universal.py` and
   `postings_utils.py`; keep pipeline modules as thin callers.
2. Remove the `scrapers` import from `postings_utils.py` by moving the
   re-processing behaviour into an explicit enrichment function.
3. Split `attributes.py`: generic detection stays; scoring helpers move to
   `processing/scoring_mechanics.py`.
4. Replace `get_added_and_removed`'s `points` injection with a neutral diff;
   let profile derivation add defaults.
5. Specify conflict rules as code plus fixtures: dates (min/max), description
   (latest non-empty), scalar fields (non-empty preserved), list fields
   (ordered union), provenance (union, never overwrite).
6. Declare `UNIVERSAL_POSTINGS` and check it at the data-layer boundary. A
   missing required field fails the merge; an unknown field passes through.
7. Backfill the universal vault from existing profile histories only as a
   dry-run artifact first; compare counts, overlaps and conflicts before writing.
   No old-data compatibility is required (Q27).
8. Keep profile fields (`points`, profile keywords, language exclusions) out of
   universal records. Old profile points are dropped when a backfill happens;
   plan only, not executed in this round (Q14).
9. Replace the absolute `REPO_ROOT_PATH` with a root derived from `__file__`;
   make every data path relative.
10. Make `save_data` atomic and use UTC timestamps; add `schema_version` to
    vault artifacts.

## Dependencies

- Phase 0 fixtures for merge and compare.
- Collection workstream for `factual_postings` ownership.
- Profiles workstream for which derived fields are generic and which are policy.

## Completion check

- Merge and diff are importable and testable without a scraper, a browser or a
  profile module.
- Repeated merge/enrich on saved fixtures is idempotent and byte-stable.
- A universal record contains no profile score, threshold or exclusion.
- A record missing a required field is rejected with the field named; a record
  with an unknown extra field passes and keeps it.
- A backfill dry run reports counts, overlaps and conflicts for review.
- No data module contains an absolute path; a write failure cannot truncate an
  existing artifact.

## Decided points

- Universal stores every posting; filtering is profile work (Q19).
- Specs live in `specs/` as code (Q20).
- Drop old profile points from universal (plan only, Q14).
- UTC, `schema_version`, atomic writes (Q12, Q13).
- No spec digest or old-data compatibility (Q27).

Implementation details left for Phase 4: chunk filename format, one vault file
per state versus a partitioned store, and whether `collection_scope.json`
remains. See [artifacts.md](../design/artifacts.md).

## Design references

- [Specs and dataclasses](../design/specs.md)
- [Artifacts](../design/artifacts.md)
- [Decisions](../design/open-questions.md)
