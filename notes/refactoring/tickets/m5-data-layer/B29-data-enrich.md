# B29 — Move generic enrichment and remove the scraper import

Status: todo · Milestone: M5 Data layer · Phase 5 · Size: M

- Depends on: B27, B28
- Files: `src/jobscraping/data/enrich.py`,
  `src/jobscraping/processing/postings_utils.py`

## Do

1. Move `enrich_postings` and its re-processing behaviour into `data/enrich.py`.
2. Remove the `BaseScraper` import from `processing/postings_utils.py`.
3. Keep enrichment idempotent: rerun replaces derived values, never appends.

## Done when

- `rg "from jobscraping.scrapers" src/jobscraping/processing` finds nothing.
- Enrichment tests pass without a browser or network.
- Double enrichment is byte-stable.
