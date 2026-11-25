# B37 — Add spec checks at stage boundaries

Status: todo · Milestone: M7 Stages · Phase 7 · Size: M

- Depends on: B36
- Files: stage modules, `specs/`

## Do

1. Check the input spec before work; report missing required fields.
2. Check the output spec before writing.
3. Allow unknown fields.

## Done when

- A stage started on data missing a required field fails before work.
- A stage with extra fields succeeds and preserves them.
- The error names the field.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
