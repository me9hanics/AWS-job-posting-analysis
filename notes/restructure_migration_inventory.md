# Restructure Migration Inventory

## Scope

`AWS-job-posting-analysis-restructured` is the clean redesign target.
`AWS-job-posting-analysis` remains the runnable baseline until this target has
passed the relevant smoke checks. Do not move or delete code in the baseline as
part of this work.

The goal is to relocate and wrap existing behavior first. Reimplement a function
only when the old function mixes responsibilities that cannot cross the new
universal/profile boundary.

## Immediate State

The scraper split has started:

- `scrapers/sites.py` has been deleted.
- `scrapers/basescraper.py` exists.
- Per-site modules exist under `scrapers/websites/` for Karriere.at,
  Raiffeisen, and Hardverapro.

The target is not importable yet because these files still refer to the deleted
`jobscraping.scrapers.sites` module:

- `src/jobscraping/scrapers/__init__.py`
- `src/jobscraping/pipelines/collecting.py`
- `src/jobscraping/processing/postings_utils.py`
- `script.py`
- `schedule/emails.py`

`scrapers/sites_postprocess.py` is an unimported, indented fragment that
duplicates methods already present in `basescraper.py`. It must not become a
second implementation of scraper post-processing.

## Target Shape

```text
src/jobscraping/
  config/                 # runtime paths, defaults, site rules
  io/                     # JSON I/O and output rendering
  pipelines/              # universal scrape and universal storage orchestration
  processing/             # profile derivation, scoring, filters, generic facts
  scrapers/
    basescraper.py         # shared scrape mechanics only
    scrape.py              # low-level HTTP/Selenium helpers
    parsing.py             # shared HTML/BeautifulSoup posting parsing
    websites/              # one concrete scraper per source site
  utils/                   # generic URL and data-structure helpers
  profiles/                # later: tech/legal/dani/tn configuration only
```

`profiles/` is useful once the first profile derivation works. Do not create a
new configuration abstraction before then; initially copy the existing profile
constants from `schedule/*_collect.py` unchanged.

## Move and Keep Inventory

### Keep in place now

- `config/configs.py` and `config/constants.py`
  - Keep as the existing source of runtime paths, scraper rules, and common
    defaults. Split profile configuration later, after the profile interface is
    proven.
- `utils/urls.py` and `utils/datastruct_utils.py`
  - Already have the correct ownership.
- `io/files_io.py`
  - Keep as low-level JSON/file I/O.
- `scrapers/scrape.py`
  - Keep as the shared HTTP/Selenium primitive layer.
- `scrapers/basescraper.py`
  - Keep as the single shared base class.
- `scrapers/websites/karriere_at.py`, `raiffeisen.py`, and `hardverapro.py`
  - Keep as the concrete site implementations.
- `processing/attributes.py` and `processing/transformations.py`
  - Keep temporarily as the source of existing behavior while narrow wrappers
    are introduced in their destination modules.
- `processing/postings_utils.py`
  - Keep temporarily for history unification and comparison helpers.

### Move next without changing implementation logic

1. Fix scraper public imports.
   - Export `BaseScraper` from `scrapers.basescraper`.
   - Export concrete classes from `scrapers.websites.*`.
   - Update `collecting.py`, `script.py`, `emails.py`, and the local import in
     `postings_utils.enrich_postings` to use those public paths.
   - This is a relocation repair, not a behavior change.

2. Move shared HTML posting parsing.
   - Move `process_posting_soups` from `processing/postings_utils.py` to
     `scrapers/parsing.py`.
   - Update `BaseScraper._process_posting_soups` to import that function from
     `scrapers.parsing`.
   - Leave a temporary re-export in `postings_utils.py` only if another caller
     still needs the old path.

3. Move scoring functions by direct relocation.
   - Move `salary_points`, `score_text_nested`, and `rank_postings` from
     `processing/attributes.py` to `processing/scoring.py`.
   - Initially make `attributes.py` re-export them if compatibility is needed.
   - Do not alter score formulas or the profile ranking dictionaries.

4. Add filter wrappers before moving filter bodies.
   - `candidate_filtering.py` should initially call the existing broad title/
     keyword selection helpers from `transformations.py`.
   - `selection_filtering.py` should initially call the existing exclusion,
     points, and date helpers from `transformations.py`.
   - Move bodies only after the derived-tech flow is stable.

5. Separate output orchestration by delegation.
   - Keep `outputs_excel.create_excel_report` as the Excel renderer.
   - Move the DataFrame preparation currently in `outputs.generate_outputs` to
     an Excel-named helper in `outputs_excel.py`.
   - Let `generate_profile_outputs.py` call that helper plus the existing
     `outputs.log_to_markdown` and optional email helper.

## Temporary Compatibility Code

These functions currently mix scraper behavior with profile processing. Keep
them as temporary compatibility methods while universal scraping is introduced:

- `BaseScraper._process_data`
- `BaseScraper._filter_postings`
- `BaseScraper._rank_postings`
- `BaseScraper._find_keywords_in_postings`
- `BaseScraper._apply_filters_transformations`

The first required change is a narrow `process=True` argument on concrete
`gather_data` methods. When `process=False`, a scraper must return scraped,
profile-neutral posting facts without calling `_process_data`.

Do not move these methods into a new `sites_postprocess.py` module. They are
temporary adapters, not a permanent scraper submodule. Once profile derivation
owns filtering, scoring, and keyword matching, remove the adapters from the
base class.

## Pipeline Migration Order

1. **Import gate**
   - Repair all deleted `scrapers.sites` imports.
   - Archive `sites_postprocess.py` and `new_sites.py`.
   - Verify package imports and the three concrete scraper imports.

2. **Universal scrape gate**
   - Implement `pipelines/scrape_universal.py` using the existing concrete
     scrapers with `process=False`.
   - Save one resumable chunk per site/query unit using `files_io.save_data`.
   - Merge chunks with existing `merge_matched_titlewords` and
     `unify_postings` behavior.
   - Do not invoke profile scoring, `points` thresholds, or profile output.

3. **Universal storage gate**
   - Implement `pipelines/store_universal.py` using `files_io` and
     `unify_postings`.
   - Add a profile-neutral comparison wrapper rather than directly using
     `get_added_and_removed`, because that helper adds default `points` and
     sorts by them.
   - Produce universal `current_postings.json`, `postings_history.json`, and
     `newly_added_postings.json`.

4. **Tech derivation gate**
   - Implement `derive_profile_postings.py` against universal current data.
   - Candidate filter: route on intersections between a posting's
     `matched_titlewords` and the tech titlewords.
   - History merge: reuse `unify_postings`.
   - Scoring: call the relocated `rank_postings` with the existing tech rules.
   - Selection: reuse the existing tech point/date/exclusion filters.
   - Run first against a separate output folder or dry-run result; do not
     overwrite the active baseline's tech files during comparison.

5. **Output gate**
   - Make `generate_profile_outputs.py` the orchestration entry point while
     delegating to the existing Excel and Markdown functions.
   - Convert the tech script only after the derived results match the expected
     output shape.

6. **Other profiles**
   - Convert legal next, then dani and tn.
   - Move each profile's constants and transformation list into
     `profiles/<name>.py` only when converting that profile.

7. **Cleanup gate**
   - Archive `pipelines/collecting.py` after no target schedule script imports
     it.
   - Archive `pipelines/pipeline.py`; it is an older experimental composition
     model and is not the target flow.
   - Archive the old per-profile `schedule/*_collect.py` scripts only after
     their replacement profile derivations have been checked.

## Files to Archive or Remove

Do not delete these now. Archive them only after their noted dependency gate:

- `scrapers/sites_postprocess.py`
  - Archive immediately after confirming its methods already exist in
    `basescraper.py`; it is currently an invalid duplicate fragment.
- `scrapers/new_sites.py`
  - Archive immediately; it is only a two-line idea placeholder.
- `pipelines/pipeline.py`
  - Archive after documenting that the universal/profile flow supersedes it.
- `schedule/universal_pipeline.py` and `schedule/universal_filter.py`
  - Archive if `schedule/scrape_universal.py` and
    `schedule/derive_profile_from_universal.py` become the only new entry
    points. Do not maintain duplicate skeleton entry points.
- `pipelines/collecting.py`
  - Archive only after all target profile scripts use universal derivation.
- `schedule/tech_collect.py`, `legal_collect.py`, `dani_collect.py`, and
  `tn_collect.py`
  - Archive only after their replacement profile entry points are verified.
- `outdated_tricks.py`
  - Archive with the legacy material; it is not part of the redesign runtime.

## Separate Pipeline

`Hardverapro` is a product-listing pipeline, not a job-profile derivation. Keep
its scraper and `schedule/hardverapro_collect.py` independent. It can reuse
low-level I/O and Excel helpers, but should not be forced into the universal
job-posting vault.

## Documentation to Update During the Import Gate

- `agents/project_briefing.md` still refers to the old `methods/` layout and
  says `sites.py` is active.
- `notes/modular_pipeline_plan.md` still describes `sites.py` as current and
  names a future `scrapers.base` module instead of the present
  `scrapers.basescraper` path.
- `scrapers/site_scrapers_plan.md` should be revised once the public imports
  point to the split modules.

Keep those documents current with the target repository only; they should not
describe the original running repository as though it were already migrated.
