# Modular Pipeline Plan

Status: package structure exists, planning skeletons exist, current runtime still
uses the legacy profile collection path.

## Current Package Layout

The old `methods/` folder has been moved into an installable package:

`src/jobscraping/`

Current module groups:

- `jobscraping.config`
  - `configs.py`: user/profile defaults, paths, scoring configuration.
  - `constants.py`: output columns, filenames, request constants, base site
    rules.

- `jobscraping.io`
  - `files_io.py`: JSON/file loading and saving helpers.
  - `outputs.py`: current mixed output orchestration, Markdown log, email.
  - `outputs_excel.py`: Excel report creation and Excel formatting helpers.
  - `generate_profile_outputs.py`: planning skeleton for future output
    orchestration.

- `jobscraping.processing`
  - `attributes.py`: salary parsing, language detection, keyword finding,
    ranking/scoring helpers.
  - `transformations.py`: current reusable filters and transformations.
  - `postings_utils.py`: current posting comparison, history unification,
    enrichment, and processing helpers.
  - `candidate_filtering.py`: skeleton for broad profile routing.
  - `selection_filtering.py`: skeleton for final relevance filtering.
  - `scoring.py`: skeleton for profile-specific scoring helpers.
  - `derive_profile_postings.py`: skeleton for deriving profile datasets from
    universal postings.

- `jobscraping.scrapers`
  - `scrape.py`: low-level HTTP/Selenium scraping helpers.
  - `sites.py`: current combined scraper file with `BaseScraper`,
    `KarriereAT`, and `Raiffeisen`.
  - `websites/karriere_at.py`: placeholder for future Karriere.at scraper.
  - `websites/raiffeisen.py`: placeholder for future Raiffeisen scraper.

- `jobscraping.pipelines`
  - `collecting.py`: current legacy orchestration, formerly `datacollect.py`.
  - `pipeline.py`: old experimental orchestration, still not the target.
  - `scrape_universal.py`: skeleton for broad universal scraping.
  - `store_universal.py`: skeleton for universal vault storage.

- `jobscraping.utils`
  - `datastruct_utils.py`: generic dictionary/data-structure helpers.
  - `urls.py`: URL construction and URL display helpers.

The package is installed with `uv pip install -e .` through `pyproject.toml`.

## Target Shape

The project should move from profile scripts that scrape independently to a
two-layer flow:

1. Universal vault: scrape broadly once and maintain a profile-neutral posting
   store.
2. Profile derivations: route, score, select, and output postings for specific
   usecases such as tech, legal, dani, and tn.

This is similar to a medallion structure:

- Bronze: raw or lightly normalized scraped postings/chunks.
- Silver: universal current/history with generic enrichment.
- Gold: profile-specific candidate histories, selected current postings, and
  outputs.

## Universal Vault

Target folder:

`data/save/postings/universal/`

Expected files:

- `current_postings.json`
- `newly_added_postings.json`
- `postings_history.json`
- `newly_added_history.md`
- later: chunk files for resumable scraping

The universal vault owns profile-neutral facts:

- posting identity
- source site
- title
- company
- URL
- locations
- description
- raw salary text
- generic salary guess
- generic language guess
- collection dates
- matched scrape titlewords or broad scrape queries

The universal vault should not own profile-specific scores such as tech points,
legal points, dani points, or tn points.

## Profile-Derived Data

Target folders:

- `data/save/postings/tech/`
- `data/save/postings/legal/`
- `data/save/postings/dani/`
- `data/save/postings/tn/`

Each profile folder keeps its own:

- `postings_history.json`: all postings that passed the profile candidate
  filter, including low-scoring records.
- `current_postings.json`: final selected postings for that profile.
- `newly_added_postings.json`: newly selected postings for that profile.
- `newly_added_history.md`: human-readable log of newly selected postings.

Profile folders own:

- candidate filtering rules
- profile-specific scoring rules
- profile-specific keywords
- final relevance thresholds
- profile-specific output generation

## Two Filter Steps

The current plan intentionally keeps two filter steps:

1. Candidate filter
   - Broad profile routing.
   - Decides whether a universal posting belongs in a profile history.
   - Example: "could this be a tech posting?"
   - This should usually happen before profile scoring.
   - Target module: `jobscraping.processing.candidate_filtering`.

2. Selection filter
   - Final relevance selection.
   - Decides whether a profile candidate belongs in current outputs.
   - Can use score thresholds, date windows, language rules, exclusions, and
     manual overrides.
   - Target module: `jobscraping.processing.selection_filtering`.

These may be merged later, but the two-step model is useful while the system is
being made modular.

## Stage Order

Universal collection:

1. Build broad scrape inputs.
2. Run site scrapers.
3. Save resumable chunks after each useful unit of work.
4. Merge chunks into universal current postings.
5. Compare against universal history.
6. Update universal history and newly-added files.

Target modules:

- `jobscraping.pipelines.scrape_universal`
- `jobscraping.pipelines.store_universal`
- `jobscraping.scrapers.*`
- `jobscraping.io.files_io`

Profile derivation:

1. Load universal current postings.
2. Load profile history.
3. Apply candidate filter.
4. Merge candidates into profile history.
5. Score profile candidates with profile-specific rules.
6. Save updated profile history with scores.
7. Apply selection filter.
8. Compare selected current postings against previous profile current/history.
9. Save profile current and newly-added files.
10. Generate requested outputs.

Target modules:

- `jobscraping.processing.derive_profile_postings`
- `jobscraping.processing.candidate_filtering`
- `jobscraping.processing.scoring`
- `jobscraping.processing.selection_filtering`
- `jobscraping.io.generate_profile_outputs`

## Implementation Split

### Scraping

Keep site-specific scraper behavior in scraper modules.

Current:

- `jobscraping.scrapers.sites.BaseScraper`
- `jobscraping.scrapers.sites.KarriereAT`
- `jobscraping.scrapers.sites.Raiffeisen`

Target:

- `jobscraping.scrapers.base.BaseScraper`
- `jobscraping.scrapers.websites.karriere_at.KarriereAT`
- `jobscraping.scrapers.websites.raiffeisen.Raiffeisen`

Before universal scraping can be clean, scraper `gather_data` methods need a
way to return raw/profile-neutral postings without profile scoring, probably:

```python
gather_data(..., process=True)
```

Universal scraping should call `process=False`.

### Generic Processing

Generic processing may include:

- salary parsing
- language detection
- keyword finding
- posting normalization
- first/last collected date handling

These belong in `jobscraping.processing` unless they become pure storage logic.

Profile-specific scoring should not happen in universal processing.

### Profile Scoring

Profile scoring belongs in `jobscraping.processing.scoring`, called from
profile derivation.

The same posting may receive different scores for tech, legal, dani, or tn, so
scores belong to profile histories and selected profile outputs, not the
universal vault.

### Storage

Low-level file operations stay in `jobscraping.io.files_io`.

Pipeline-stage storage belongs in:

- `jobscraping.pipelines.store_universal` for universal vault state.
- `jobscraping.processing.derive_profile_postings` for profile history/current
  state, unless that grows large enough to deserve `store_profile.py`.

### Outputs

Current output generation still mainly goes through `jobscraping.io.outputs`.

Target split:

- `jobscraping.io.outputs_excel`: Excel-specific DataFrame preparation and
  workbook creation.
- `jobscraping.io.outputs`: Markdown/email/general output helpers.
- `jobscraping.io.generate_profile_outputs`: profile output orchestration.

## Current Legacy Runtime

Current profile scripts under `schedule/` still call:

`jobscraping.pipelines.collecting.get_postings`

That means the live runtime is still the legacy profile-specific scrape,
process, compare, store, and output path. The skeleton modules describe the new
direction but are not yet wired into daily collection.

## What Is Already Done

- `methods/` moved to `src/jobscraping/`.
- Package imports use `jobscraping.*`.
- Editable install with `uv pip install -e .` works.
- `jobscraping.utils.urls` and `jobscraping.utils.datastruct_utils` exist.
- Skeletons exist for universal scraping, universal storage, profile derivation,
  profile output generation, candidate filtering, selection filtering, and
  scoring.
- Schedule imports have been updated to the package namespace.

## Next Implementation Milestones

1. Split Excel output orchestration from `jobscraping.io.outputs` into
   `jobscraping.io.outputs_excel`.
2. Move scoring helpers from `jobscraping.processing.attributes` into
   `jobscraping.processing.scoring`.
3. Move broad routing helpers from `transformations.py` into
   `candidate_filtering.py`.
4. Move final relevance filters from `transformations.py` into
   `selection_filtering.py`.
5. Add `process=False` support to scraper `gather_data` methods.
6. Extract universal storage helpers from `collecting.py` into
   `store_universal.py`.
7. Implement `scrape_universal.py` against existing scraper classes.
8. Implement `derive_profile_postings.py`.
9. Convert one profile, likely `tech`, to derive from universal data.
10. After one profile works, split `jobscraping.scrapers.sites` into base and
    per-site modules.
