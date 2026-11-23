# B44 — Remove compatibility code and stale modules

Status: todo · Milestone: M9 Done · Phase 9 · Size: M

- Depends on: B43
- Files: `scrapers/sites.py` shim, empty modules, `pipelines/collecting.py`,
  unused schedule scripts

## Do

1. Remove re-exports with no named caller (Q16).
2. Archive or delete superseded entry points.
3. Keep one documented way to run collection, derivation and outputs.

## Done when

- No module is imported only for compatibility.
- No duplicate scraper or empty placeholder remains.
- The suite passes.
