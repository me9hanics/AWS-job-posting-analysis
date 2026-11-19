# B15 — Update every importer

Status: todo · Milestone: M3 One scraper per site · Phase 2 · Size: S

- Depends on: B14
- Files: `pipelines/collecting.py`, `processing/postings_utils.py`,
  `script.py`, `schedule/emails.py`, `schedule/*_collect.py`

## Do

1. Replace `from jobscraping.scrapers import sites` with the public
   `BaseScraper`/site imports.
2. Keep `schedule/hardverapro_collect.py` untouched (archive-only, Q17).
3. Leave no import of a deleted module.

## Done when

- `rg "scrapers import sites|scrapers.sites"` finds only the intentional
  compatibility shim, if one still exists.
- The suite passes.
