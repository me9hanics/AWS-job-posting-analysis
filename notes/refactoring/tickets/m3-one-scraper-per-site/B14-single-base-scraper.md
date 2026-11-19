# B14 — Make `BaseScraper` single-source and shrink `sites.py`

Status: todo · Milestone: M3 One scraper per site · Phase 2 · Size: M

- Depends on: B13
- Files: `src/jobscraping/scrapers/basescraper.py`,
  `src/jobscraping/scrapers/sites.py`, `scrapers/__init__.py`

## Do

1. Choose one `BaseScraper` body and delete the duplicate.
2. `sites.py` becomes a compatibility re-export only, or is removed if no caller
   still needs it (Q16).
3. Keep public names stable through `scrapers/__init__.py`.

## Done when

- `rg "class BaseScraper"` returns one match.
- `rg "class KarriereAT|class Raiffeisen"` returns one match each.
- The suite and fixture tests pass.
