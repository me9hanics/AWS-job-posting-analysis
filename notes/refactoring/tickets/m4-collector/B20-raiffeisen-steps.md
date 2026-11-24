# B20 — Give `Raiffeisen` declared steps

Status: todo · Milestone: M4 Collector · Phase 4 · Size: M

- Depends on: B13, B19
- Files: `scrapers/websites/raiffeisen.py`

## Do

1. Same split as B19, using Raiffeisen's actual flow.
2. Keep a single-step path if that is what the site actually does.
3. Keep the legacy wrapper until B24.
4. Follow B19's shape: steps are bound methods, site differences are arguments
   or `rules` keys, and nothing is added to or overridden on `BaseScraper`
   (Q30). Raiffeisen's `_process_posting_soups`/`_next_page_logic` equivalents
   become parsing/pagination calls with their own arguments.

## Done when

- The adapter exposes its steps in order.
- Fixture parity holds.
- The two site modules do not share a hidden "main" step.
- Neither site class overrides a method of `BaseScraper`.
