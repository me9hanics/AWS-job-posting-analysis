# B18 — Extract pagination and retire the facade

Status: todo · Milestone: M3 One scraper per site · Phase 3 · Size: S

- Depends on: B17
- Files: `src/jobscraping/scrapers/pagination.py`, `scrapers/scrape.py`

## Do

1. Move URL construction and next-page rules.
2. Update internal imports to `http`/`browser`/`pagination`.
3. Remove `scrape.py` if no caller outside the package needs it; otherwise keep a
   thin re-export and note the caller.

## Done when

- Pagination tests pass.
- `scrape.py` is either gone or contains only re-exports.
- No site module contains HTTP/session code.
