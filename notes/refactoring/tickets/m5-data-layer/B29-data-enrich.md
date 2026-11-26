# B29 — Move generic enrichment and remove the scraper import

Status: done · Milestone: M5 Data layer · Phase 5 · Size: M

- Depends on: B27, B28
- Files: `src/jobscraping/data/enrich.py`, `src/jobscraping/data/language.py`,
  `src/jobscraping/data/salary.py`, `src/jobscraping/processing/postings_utils.py`,
  `src/jobscraping/processing/attributes.py`,
  `src/jobscraping/processing/language_requirements.py`

## Do

1. Move the detection primitives down into `data`: `analyze_text_language`
   and the `language_requirements` content to `data/language.py`; salary
   detection to `data/salary.py`. `data` must not import `processing`.
   `processing` re-exports the old public names as shims; B44 removes them.
2. Move `enrich_postings` into `data/enrich.py` without the `BaseScraper`
   import or profile reprocessing; it has no callers today, so no reprocessing
   hook is carried over.
3. Keep enrichment idempotent: rerun replaces derived values, never appends.
4. Move `get_date_of_collection` here from `postings_utils`; enrichment is its
   only consumer.
5. Add the profile-neutral annotation pass (Q29): fill `language`
   (`analyze_text_language`) and `guessed_required_languages`
   (`guess_required_languages`) on records with a description, replacing previous
   values rather than merging.
6. Let the annotations survive the fact projection: add both names to
   `RAW_POSTING_FIELDS` (or its successor) so `factual_postings` keeps them on
   already-annotated records.

## Implementation notes

`language` currently appears in `_process_data` (legacy scraper path) and inside
`derive_profile_postings`; both are profile-driven call sites. In the target
flow the data layer owns the fact and derivation only reads it (B33). Keep the
legacy behaviour working until the cutover: the annotation function is additive,
so the legacy path recomputing the same values is harmless.

`factual_postings` projects to `RAW_POSTING_FIELDS`, so the annotations must be
in that set or every derivation call strips them before B33 can consume them.
Adding them changes no current output: raw collection records do not carry the
fields yet, and the legacy path recomputes them afterwards.

## Done when

- `rg "from jobscraping.scrapers" src/jobscraping/processing` finds nothing.
- Enrichment tests pass without a browser or network.
- Double enrichment is byte-stable.
- A record with a description gains both fields; a second run is identical.
- `factual_postings` keeps both fields instead of stripping them.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
