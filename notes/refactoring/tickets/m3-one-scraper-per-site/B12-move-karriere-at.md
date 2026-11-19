# B12 — Move `KarriereAT` to its site module

Status: todo · Milestone: M3 One scraper per site · Phase 2 · Size: M

- Depends on: B11
- Files: `src/jobscraping/scrapers/websites/karriere_at.py`,
  `src/jobscraping/scrapers/sites.py`, `scrapers/__init__.py`

## Do

1. Move the canonical class body unchanged.
2. Export it from `websites/__init__.py` and `scrapers/__init__.py`.
3. Keep a temporary re-export from `sites.py` so existing imports work.

## Done when

- `KarriereAT` is defined in exactly one file.
- Fixture parsing is unchanged.
- Existing call sites still import successfully.
