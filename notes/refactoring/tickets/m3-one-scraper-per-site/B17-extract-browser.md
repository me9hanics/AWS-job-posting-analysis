# B17 — Extract the headless-browser path

Status: done · Milestone: M3 One scraper per site · Phase 3 · Size: M

- Depends on: B16
- Files: `src/jobscraping/scrapers/browser.py`, `scrapers/scrape.py`

## Do

1. Move Selenium session setup, popups and scrolling into `browser.py`.
2. Keep the facade re-exports.
3. Ensure no HTTP-only caller imports Selenium.

## Done when

- `browser.py` imports no `requests` request path.
- Scraper fixture tests pass.
- `http.py` contains no Selenium import (checked in source; a `sys.modules`
  assertion cannot hold while `scrapers/__init__.py` imports `BaseScraper`).
