# B22 — Create the universal collector

Status: todo · Milestone: M4 Collector · Phase 4 · Size: L

- Depends on: B09, B10, B19, B20, B21
- Files: `src/jobscraping/acquisition/collector.py`

## Do

1. Implement `run_collection(adapters, config)`.
2. Iterate sites, queries and locations; run each adapter's steps in order;
   honor `CollectionConfig.steps`; merge by identity.
3. Record step outcomes and errors in a run report structure.
4. Do not store files here; return records plus the report.

## Done when

- A one-step and a two-step adapter both run.
- Skipping a step is observable.
- Zero records is a failure.
- The collector imports no profile and no site module by name.
