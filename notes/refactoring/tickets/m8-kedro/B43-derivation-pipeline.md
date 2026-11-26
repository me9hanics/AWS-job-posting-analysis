# B43 — Build derivation and outputs; parity check

Status: todo · Milestone: M8 Kedro · Phase 8 · Size: L · User-owned

- Depends on: B42, B36
- Files: `pipelines/derivation/`, `pipelines/outputs/`, user-owned

## Do

1. One parameterised derivation pipeline for every profile.
2. Excel as a dataset; Markdown/email as side effects.
3. Run the script path and Kedro path on the same inputs.
4. Add no Dani-only node and no Dani-only pipeline function. A profile differs
   from another only in `conf/` (parameters, catalog overrides, `--params`) plus
   its `profiles/<name>.py` functions, such as candidate and scoring rules. If
   Dani needs behaviour no parameter expresses, add the parameter or the profile
   function, not a branch on the profile name.

## Done when

- Artifacts match byte-for-byte excluding timestamps.
- `kedro run --pipeline=derivation --params=profile:dani` works.
- No profile constants live in pipeline modules, and no pipeline module holds a
  function, node or branch that exists for one profile only; a second profile
  run is a parameter/catalog change (D26).
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
