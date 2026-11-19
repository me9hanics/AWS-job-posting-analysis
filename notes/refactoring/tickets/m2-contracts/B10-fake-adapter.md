# B10 — Prove the step contract with a fake adapter

Status: todo · Milestone: M2 Contracts · Phase 1 · Size: S

- Depends on: B09
- Files: `tests/test_steps_contract.py` (new)

## Do

1. Define a fake one-step adapter and a fake two-step adapter in the test.
2. Exercise order, skip-by-name, a raising step, and zero records with a
   test-local runner.
3. Confirm the contract can express both site shapes without a collector.

## Done when

- The test passes and needs no network, browser or profile.
- The collector ticket (B22) can copy the test's call shape.
