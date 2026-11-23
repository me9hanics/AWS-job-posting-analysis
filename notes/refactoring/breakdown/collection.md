# Collection workstream

Status: decided 2026-11-16; no move performed.

Owns everything between "a query exists" and "raw profile-neutral facts are
saved as chunks". It does not own scoring, selection, profile history or output.

## Current state

- `scrapers/sites.py` is the active implementation: `BaseScraper` plus two site
  classes in one module. `scrapers/__init__.py` exports from it, and
  `pipelines/collecting.py`, `processing/postings_utils.py` and `script.py`
  import it.
- `scrapers/basescraper.py`, `scrapers/websites/karriere_at.py` and
  `scrapers/websites/raiffeisen.py` are parallel copies. `websites/__init__.py`
  exports nothing. No runtime uses the split modules.
- `scrapers/scrape.py` mixes HTTP requests, Selenium sessions, popup handling,
  scrolling and pagination heuristics.
- `BaseScraper` still owns profile behaviour through `_filter_postings`,
  `_rank_postings`, `_find_keywords_in_postings`, `_apply_filters_transformations`
  and `_process_data`.
- `gather_data` is monolithic per site. A site cannot declare separate steps,
  cannot skip an expensive step, and cannot emit an extra export (for example a
  company list).
- `collecting.py` holds reusable acquisition helpers (`scrape_sites`,
  `validate_postings_quality`) next to the legacy profile pipeline.
- `scrape_universal.py::run_universal_scrape_flow` is the collector equivalent:
  it loops over adapters and units, but also owns scope, cache and storage.
- `schedule/hardverapro_collect.py` imports a missing
  `scrapers.websites.hardverapro` module. Archive-only one-off; not a gate.
- More sites are planned soon. Today each one would start as another copied
  `BaseScraper` variant, which is the cost this workstream removes.

## Target

Five separable parts:

1. **Mechanics** — one HTTP path, one headless-browser path, one pagination
   helper. No posting schema, no profile knowledge.
2. **Parsing** — HTML/JSON payload → neutral posting facts. Pure where possible.
3. **Site adapters with steps** — per-source modules that own selectors, parsing
   and an ordered step list. A one-shot site exposes a single step; a
   listing/detail site exposes two. Steps and their names are adapter-defined;
   no required/optional flags. See
   [collection-steps.md](../design/collection-steps.md).
4. **Universal collector** — iterate sites and query units, apply step
   selection, merge results, apply quality gates, write chunks and record
   failures in a JSON run report.
5. **Exports and BI views** — company lists and similar are derived from records
   when needed; they are not pipeline datasets.

Shared enrichment (salary parsing, language detection) is not collection in this
design: it belongs to the data/generic layer, so that facts can be re-enriched
without scraping. A salary extraction can still be an explicit adapter step when
it needs the raw page; the distinction is whether it can run on saved facts.

Every adapter must be addable as one module plus one registry entry. If a new
site needs a collector change, the seam is wrong.

## Changes

1. Choose one `BaseScraper` and one per-site module; delete or archive the
   duplicate bodies after a fixture comparison proves equivalence.
2. Export only the split modules from `scrapers/__init__.py`; update
   `collecting.py`, `postings_utils.py`, `script.py` and `schedule/emails.py`.
3. Move `process_posting_soups` and site-agnostic extraction into a parsing
   module.
4. Split `scrape.py` into HTTP and headless-browser paths plus shared
   pagination. Keep `scrape.py` as a facade during the move.
5. Define the adapter step list in each site module: ordered `(name, callable)`
   pairs, one or two in practice. A `Step` dataclass is optional; do not add
   required flags or enforcement.
6. Make step selection part of `CollectionConfig` (YAML). Any step may be
   skipped; the next stage's input spec decides whether the result is usable.
7. Extract the universal collector from `scrape_universal.py` and
   `collecting.py` into `acquisition/collector.py::run_collection`: adapter
   loop, step selection, unit merge, quality gates, chunks and JSON run report.
   Leave scope/cache/storage helpers callable.
8. Extract `scrape_sites` and `validate_postings_quality` from `collecting.py`
   into the collector/quality modules; `scrape_universal.py` then composes the
   collector with storage only.
9. Remove the profile-processing methods from `BaseScraper` once derivation owns
   filtering and scoring. Replace the `process` flag with step selection.
10. Keep the two-step pattern from the current sites: listing facts first, detail
    facts second. Name the steps after what the site does, not after a global
    vocabulary.
11. Company lists and similar are exports or BI views derived later. Do not add
    a side dataset, step artifact or parallel pipeline now.

## Dependencies

- Phase 0 fixtures before deleting duplicates.
- Data workstream for `factual_postings`, data specs and enrichment ownership.
- Pipelines workstream for chunk artifacts, step selection and quality-gate
  failure behaviour.

## Completion check

- Exactly one implementation of `BaseScraper` and of each site class exists.
- All production imports use public scraper paths; no import of a deleted
  module remains.
- A saved fixture per site produces the same facts before and after the move.
- One single-shot adapter and one two-step adapter both run through the
  collector.
- Adding a sample site requires one module and one registration entry; no
  collector, data or profile edit.
- A skipped step produces a partial result that the next stage accepts or
  rejects explicitly, never silently.
- A failed step is named in the JSON run report and the run continues; zero
  records is a failure, not an empty success.
- Raw output contains no profile scores, no profile exclusions and no
  profile-specific keywords.
- A first-page failure and a terminal pagination state are distinguishable in
  the returned step outcome rather than in a `process=False` branch.

## Decided points

- Steps are adapter-defined and lightweight; no required/optional flags (Q11).
- HTTP and headless-browser paths are separate (Q2).
- Side outputs are exports, not datasets (Q18).
- Hardverapro is archive-only (Q17).
- The collector is `acquisition/collector.py::run_collection` (Q26).

The only open design question is Q16, the compatibility layer. See
[open-questions.md](../design/open-questions.md#still-open).

## Design references

- [Collection steps](../design/collection-steps.md)
- [Module seams](../design/module-seams.md)
- [Specs and dataclasses](../design/specs.md)
- [Artifacts](../design/artifacts.md)
- [Decisions](../design/open-questions.md)
