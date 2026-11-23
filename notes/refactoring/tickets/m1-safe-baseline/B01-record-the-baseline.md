# B01 — Record the baseline

Status: todo · Milestone: M1 Safe baseline · Phase 0 · Size: S

- Depends on: —
- Files: [breakdown/migration.md](../../breakdown/migration.md)

## Do

1. Fill the baseline section with the live entry points, the importers of
   `scrapers.sites` and `collecting.get_postings`, the saved-data layout, and the
   current test command.
2. Record every absolute path and where it comes from.
3. Note which schedule scripts are archive-only.

## Done when

- The baseline section has no `TBD` and matches `rg` output.
- The test command is written down.
- Archive-only scripts are named so they do not become gates.

## Notes

The 2026-11-16 review already established most of this. Verify against the live
tree and update the status notes; do not redo the investigation.
