# B43 — Build derivation and outputs; parity check

Status: todo · Milestone: M8 Kedro · Phase 8 · Size: L · User-owned

- Depends on: B42, B36
- Files: `pipelines/derivation/`, `pipelines/outputs/`, user-owned

## Do

1. One parameterised derivation pipeline for every profile.
2. Excel as a dataset; Markdown/email as side effects.
3. Run the script path and Kedro path on the same inputs.

## Done when

- Artifacts match byte-for-byte excluding timestamps.
- `kedro run --pipeline=derivation --params=profile:dani` works.
- No profile constants live in pipeline modules.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
