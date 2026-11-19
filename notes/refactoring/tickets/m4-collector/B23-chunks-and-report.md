# B23 — Add chunk artifacts and the JSON run report

Status: todo · Milestone: M4 Collector · Phase 4 · Size: M

- Depends on: B22
- Files: `src/jobscraping/acquisition/chunks.py`,
  `src/jobscraping/acquisition/collector.py`

## Do

1. Write one chunk per completed site/query/location/step unit.
2. Use the scope digest in the path; do not write an empty chunk for a failed
   unit.
3. Write the JSON run report with unit, step, outcome and error.
4. Leave atomic writes for B30; use the current save helper for now.

## Done when

- A skipped step has no chunk.
- A failed step is named in the report.
- Rerunning the same unit replaces its chunk, not duplicates it.
