# B25 — Collector integration tests

Status: todo · Milestone: M4 Collector · Phase 4 · Size: M

- Depends on: B24
- Files: `tests/test_collector.py` (extends the module created in B22)

## Do

1. One-shot adapter and two-step adapter through `run_collection`.
2. Skip the detail step; assert partial records and the report.
3. A step raises; assert the run continues where possible and names the error.
4. Zero records; assert failure.
5. Register a fake new site and prove no collector edit is needed.

## Implementation notes

Five cases in the existing `tests/test_collector.py`: a one-shot adapter and a
two-step adapter; skipping `details` (assert the partial records, the `skipped`
status, and no chunk under a temporary artifact path); a raising step (assert
later steps still ran, the error text is in the report, and other adapters'
records survive); an adapter that returns nothing (`zero_records` and
`failed`); and a fake new site defined in the test module plus one registry
entry (`ADAPTERS = [FakeNewSite]`) with no collector edit.

The fake new site shape is the requirement, not a fixture convenience: one
module with `source` and `steps`, one entry in the adapter list. See
[implementation-flow.md](implementation-flow.md#b25--collector-integration-tests).

## Done when

- All five cases pass.
- The fake site is one module plus one registry entry.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
