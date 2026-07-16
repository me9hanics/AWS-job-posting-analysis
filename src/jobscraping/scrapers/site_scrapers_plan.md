# Site Scraper Split Plan

Status: the split files exist, but they are not yet wired into the active
collection runtime.

`src/jobscraping/scrapers/sites.py` still combines the base scraper and concrete
site scrapers for compatibility with the current pipeline. The target direction
is one concrete site module per scraper.

## Target Folder

`src/jobscraping/scrapers/websites/`

## Current and Target Files

- `basescraper.py`
  - Current home of `BaseScraper`.
  - Shared loading, salary parsing, processing adapters, and common scrape
    utilities.

- `websites/karriere_at.py`
  - Exists as the future home of `KarriereAT`.
  - Karriere-specific HTTP/JSON scraping, cookies, CSRF headers, result parsing,
    and detail-description parsing.

- `websites/raiffeisen.py`
  - Exists as the future home of `Raiffeisen`.
  - Raiffeisen-specific HTML listing scraping, pagination, detail-page parsing,
    and description extraction.

- `websites/__init__.py`
  - Future public exports for per-site scraper classes.
  - Should let callers import scraper classes from one stable package path.

## Migration Rule

Keep `sites.py` as a compatibility module until `collecting.py` and the active
schedule scripts import the split modules. Switch the public exports only after
the modular pipeline boundaries are clear and the collection flow has been
verified.

## Future Function-Level Needs

Even if scraper classes remain, orchestration around them should be function
based:

- build scraper config
- instantiate scraper
- run one scraper chunk
- normalize scraper output
- save scraper chunk
- merge scraper chunks

The scraper classes should only own site-specific behavior.
