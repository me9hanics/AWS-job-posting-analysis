I researched the existing merge/enrich/data-manipulation paths. I did not edit files.

**Existing Pieces**
- Main run merge: [collecting.py](C:/GitHubRepo/REPOS/AWS-job-posting-analysis-restructured/src/jobscraping/pipelines/collecting.py:90) `get_postings()` scrapes, compares current results to previous history, saves `current_postings.json`, rebuilds history via `unify_postings()`, and saves `newly_added_postings.json`.
- History merge: [postings_utils.py](C:/GitHubRepo/REPOS/AWS-job-posting-analysis-restructured/src/jobscraping/processing/postings_utils.py:188) `unify_postings()` loads JSON files from a folder and merges duplicate posting IDs. It preserves earliest `first_collected_on`, latest `last_collected_on`, fills missing fields, merges `matched_titlewords`, and updates description from the latest seen record.
- Difference detection: [postings_utils.py](C:/GitHubRepo/REPOS/AWS-job-posting-analysis-restructured/src/jobscraping/processing/postings_utils.py:46) `get_added_and_removed()` compares dict keys. Useful, but it mutates postings by adding `points=0` when missing.
- Re-enrichment/rerun processing: [postings_utils.py](C:/GitHubRepo/REPOS/AWS-job-posting-analysis-restructured/src/jobscraping/processing/postings_utils.py:320) `enrich_postings()` can reload old postings, re-derive salary fields, then rerun `process_data()`.
- Processing chain: [postings_utils.py](C:/GitHubRepo/REPOS/AWS-job-posting-analysis-restructured/src/jobscraping/processing/postings_utils.py:296) `process_data()` currently combines filtering, language detection, ranking, keyword finding, and transformations.
- Filters/manipulations: [transformations.py](C:/GitHubRepo/REPOS/AWS-job-posting-analysis-restructured/src/jobscraping/processing/transformations.py:9) has reusable filters like `select_keywords`, `filter_out_keywords`, `filter_on_points`, `filter_on_date`, and `add_postings`.
- Scratch/legacy: [outdated_tricks.py](C:/GitHubRepo/REPOS/AWS-job-posting-analysis-restructured/outdated_tricks.py:15) contains old history reconstruction, old rescoring snippets, old `unify_postings`, ranking-format conversion, and external first-collected inheritance.

**Important Findings**
- `data/save/postings/universal/` exists but is empty.
- Current profile histories have overlap. From local JSON: tech `13,427`, legal `3,006`, dani `4,751`, tn `1,763`; total unique historical posting IDs across those four is `20,834`.
- Overlaps exist, e.g. tech/legal `485`, tech/tn `747`, dani/tn `571`. So universal backfill is worthwhile.
- `points`, `keywords`, and often `matched_titlewords` are profile-specific today. They should not be blindly merged into universal as top-level truth.
- `tn_collect.py` passes `inherit_first_collected_from`, but live `get_postings()` does not use it. That logic only exists in `outdated_tricks.py`, so it is probably dead right now.
- `outdated_tricks.py` is not import-safe: it executes undefined variables like `folder_path`/`path` and uses old `methods.*` imports.

**Recommended Organization**
Create a small data-operations layer separate from scraping:

- `jobscraping/data/store.py`: load/save/list posting JSON files.
- `jobscraping/data/merge.py`: pure merge/compare/history functions.
- `jobscraping/data/enrich.py`: rerunnable generic enrichment, e.g. salary, language, normalized fields.
- `jobscraping/profiles/derive.py`: candidate filter, profile scoring, selection filter.
- `jobscraping/cli/data_ops.py`: optional commands for manual manipulation outside the pipeline.

Keep these operations independently runnable:
- `rebuild-history --profile tech`
- `rebuild-universal --profiles tech legal dani tn`
- `enrich --input ... --output ...`
- `derive-profile --profile tech --from-universal`
- `compare --new ... --previous ...`

**Universal Merge Plan**
Build universal from existing histories first, no scraping:

1. Load `postings_history.json` for `tech`, `legal`, `dani`, `tn`.
2. Merge by stable posting key, currently e.g. `karriere.at7818416`.
3. Universal top-level fields: `title`, `company`, `source`, `id`, `url`, `locations`, `description`, salary fields, language, `first_collected_on`, `last_collected_on`, `timespan_days`.
4. Merge rules: earliest first date, latest last date, latest non-empty description, union list fields like locations, preserve non-empty scalar fields.
5. Move profile-specific fields under metadata, or omit them:
   `profile_seen.tech = {first_collected_on, last_collected_on, old_points, old_keywords}`.
6. Save to `data/save/postings/universal/postings_history.json`.
7. Derive `universal/current_postings.json` separately from records active in any profile current file.

I would not wire this into the live scraping scripts first. I’d first extract and test the pure merge functions, then run a dry-run summary against the current local data.