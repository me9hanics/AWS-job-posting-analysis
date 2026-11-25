# B20 — Give `Raiffeisen` declared steps

Status: done · Milestone: M4 Collector · Phase 4 · Size: M

- Depends on: B13, B19
- Files: `scrapers/websites/raiffeisen.py`

## Do

1. Same split as B19, using Raiffeisen's actual flow.
2. Keep a single-step path if that is what the site actually does.
3. Keep the legacy wrapper (B19's lifetime note: the universal path leaves it in
   B24; the legacy profile path keeps it until B44).
4. Follow B19's shape: steps are bound methods, site differences are arguments
   or `rules` keys, and nothing is added to or overridden on `BaseScraper`
   (Q30). Raiffeisen's `_process_posting_soups`/`_next_page_logic` equivalents
   become parsing/pagination calls with their own arguments.

## Implementation notes

Same shape as B19, with Raiffeisen's actual two-step flow. The site-specific
parsers stop being class members: `_construct_page_urls`,
`_process_posting_soups`, `_next_page_logic` and `_salary_from_text` become
module functions in `raiffeisen.py` (`page_urls`, `parse_listing_soups`,
`pagination.next_page_logic_by_length`, `attributes.salary_from_text`). The
retained `gather_data` is the only base-name override left, and its
`process=True` body keeps today's batched detail fetch.

`listings` uses `parse_listing_soups` and keeps `collected_on` and
`matched_titlewords` from the page/URL as today. `details` is the raw-path
per-posting fetch (one request per miss, so one failed detail cannot shift
another ID's soup) behind the same `split_cached_postings` call as B19.

Tests: retarget `RaiffeisenHelperParsingTests` in
`tests/test_scraper_fixtures.py` at the module functions; fixture facts are
unchanged. See
[implementation-flow.md](implementation-flow.md#b20--raiffeisen-declared-steps).

## Done when

- The adapter exposes its steps in order.
- Fixture parity holds.
- The two site modules do not share a hidden "main" step.
- Neither site class overrides a method of `BaseScraper`; the temporary
  `gather_data` wrapper is the single exception.
