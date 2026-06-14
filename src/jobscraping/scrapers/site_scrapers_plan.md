# Site Scraper Split Plan

Status: planning skeleton, not wired into runtime.

`methods/sites.py` currently mixes the base scraper and concrete site scrapers in
one large file. The target direction is a folder with one module per scraper.

## Target Folder

`methods/site_scrapers/`

## Target Files

- `base.py`
  - Future home of `BaseScraper`.
  - Shared loading, salary parsing, ranking helper adapters, and common scrape
    utilities.

- `karriere_at.py`
  - Future home of `KarriereAT`.
  - Karriere-specific HTTP/JSON scraping, cookies, CSRF headers, result parsing,
    and detail description parsing.

- `raiffeisen.py`
  - Future home of `Raiffeisen`.
  - Raiffeisen-specific HTML listing scraping, pagination, detail page parsing,
    and description extraction.

- `__init__.py`
  - Public exports for scraper classes.
  - Lets callers import scraper classes from one stable package path.

## Migration Rule

Do not move scraper code until the modular pipeline boundaries are clearer.
When moved, keep compatibility aliases if old code still imports from
`methods.sites`.

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
