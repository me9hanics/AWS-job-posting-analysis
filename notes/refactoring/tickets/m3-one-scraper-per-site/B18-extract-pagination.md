# B18 — Extract pagination and retire the facade

Status: done · Milestone: M3 One scraper per site · Phase 3 · Size: S

- Depends on: B17
- Files: `src/jobscraping/scrapers/pagination.py`, `scrapers/scrape.py`

## Do

1. Move the next-page **rule** into `pagination.py`. URL construction stays per
   site because it differs per site (query parameters for `KarriereAT`, base path
   plus extension for `Raiffeisen`); per-site differences are arguments (Q30).
2. Update internal imports to `http`/`browser`/`pagination`.
3. Remove `scrape.py` if no caller outside the package needs it; otherwise keep a
   thin re-export and note the caller.

## Done when

- Pagination tests pass.
- `scrape.py` is either gone or contains only re-exports.
- No site module contains HTTP/session code.

## Implementation notes

A site may keep a one-line delegate such as `_next_page_logic` until B20 reshapes
it; that delegate is not a pagination seam.
