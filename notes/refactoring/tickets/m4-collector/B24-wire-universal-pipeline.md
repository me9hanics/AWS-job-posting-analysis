# B24 — Wire the universal pipeline to the collector

Status: todo · Milestone: M4 Collector · Phase 4 · Size: M

- Depends on: B22, B23
- Files: `src/jobscraping/pipelines/scrape_universal.py`,
  `src/jobscraping/pipelines/collecting.py`

## Do

1. Replace the ad-hoc `scrape_sites` loop in the universal path with
   `run_collection`.
2. Keep scope building, cache loading and storage in the pipeline for now.
3. Leave the legacy `get_postings` path working.

## Done when

- The universal flow produces the same final facts as before.
- The legacy profile scripts still pass their tests.
- The pipeline contains no site-specific branch.
