# B13 — Move `Raiffeisen` to its site module

Status: todo · Milestone: M3 One scraper per site · Phase 2 · Size: M

- Depends on: B12
- Files: `src/jobscraping/scrapers/websites/raiffeisen.py`,
  `src/jobscraping/scrapers/sites.py`

## Do

1. Same move and parity check as B12.
2. Keep the `sites.py` re-export until B15/B44.

## Done when

- `Raiffeisen` is defined in exactly one file.
- Fixture parsing is unchanged.
