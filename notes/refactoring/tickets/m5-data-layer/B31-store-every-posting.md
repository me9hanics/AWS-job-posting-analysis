# B31 — Store every posting in universal

Status: todo · Milestone: M5 Data layer · Phase 5 · Size: M

- Depends on: B22, B24, B27
- Files: `scrapers/basescraper.py`, `pipelines/scrape_universal.py`,
  `data/merge.py`, tests

## Do

1. Make the universal path stop running role/manager/relevance filtering;
   profiles own it.
2. Keep the legacy profile path behaviour until its cutover; do not change
   `get_postings` in this ticket.
3. Keep only factual normalization and quality gates on the universal path.
4. Ensure a posting that a profile would reject still appears in universal.

## Done when

- A fixture with a manager/irrelevant title is stored in universal.
- The same posting can be rejected by a profile.
- The legacy profile tests still pass.
- No profile field appears in universal records.
