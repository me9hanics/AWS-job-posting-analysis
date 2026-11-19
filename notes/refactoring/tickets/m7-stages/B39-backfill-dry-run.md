# B39 — Backfill dry run

Status: todo (optional, off the critical path) · Milestone: M7 Stages · Phase 7 · Size: M

- Depends on: B30, B31
- Files: `analysis/` or a one-off script

## Do

1. Read existing profile histories.
2. Report counts per profile, unique IDs, overlaps, conflict examples and fields
   that would be dropped.
3. Do not write to the live vault.

## Done when

- A reviewable dry-run JSON exists.
- No live file is modified.
- Q14 remains a plan, not an executed migration.
