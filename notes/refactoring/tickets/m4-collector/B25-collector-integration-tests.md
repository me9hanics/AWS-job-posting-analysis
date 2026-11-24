# B25 — Collector integration tests

Status: todo · Milestone: M4 Collector · Phase 4 · Size: M

- Depends on: B24
- Files: `tests/test_collector.py` (new)

## Do

1. One-shot adapter and two-step adapter through `run_collection`.
2. Skip the detail step; assert partial records and the report.
3. A step raises; assert the run continues where possible and names the error.
4. Zero records; assert failure.
5. Register a fake new site and prove no collector edit is needed.

## Done when

- All five cases pass.
- The fake site is one module plus one registry entry.
