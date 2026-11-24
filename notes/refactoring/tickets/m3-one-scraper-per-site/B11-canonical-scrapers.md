# B11 — Choose the canonical scraper implementations

Status: done · Milestone: M3 One scraper per site · Phase 2 · Size: M

- Depends on: B05
- Files: [design/module-seams.md](../../design/module-seams.md),
  `scrapers/sites.py`, `scrapers/basescraper.py`, `scrapers/websites/*`

## Do

1. Compare the active `sites.py` classes with `basescraper.py` and the
   `websites/*` variants.
2. Record which copy is canonical for `BaseScraper`, `KarriereAT` and
   `Raiffeisen`, and why.
3. Run the B05 fixtures against the chosen copy.

## Done when

- The decision is written in `design/module-seams.md`.
- The chosen copy passes the parser parity fixtures.
- No third copy remains to "merge later".

## Notes

Q16 (compatibility shim) is decided here or in B19, whichever moves the first
caller.
