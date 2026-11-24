# B16 — Extract the HTTP path

Status: done · Milestone: M3 One scraper per site · Phase 3 · Size: M

- Depends on: B15
- Files: `src/jobscraping/scrapers/http.py`, `src/jobscraping/scrapers/scrape.py`

## Do

1. Move the `requests`/response path into `http.py`.
2. Keep public helper names re-exported from `scrape.py`.
3. Add a fixture test for one request/parse path without network.

## Done when

- `http.py` imports no Selenium.
- Callers outside the scraper package are unchanged.
- Fixture tests pass.
