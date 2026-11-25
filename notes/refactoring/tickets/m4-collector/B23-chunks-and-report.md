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

## Implementation notes

In M4 a unit is one adapter: `listings` owns its query × location loops and
`Step.run` receives no unit argument. The chunk path is therefore
`chunks/<scope-digest>/<source>/<step>.json`, one file per completed step, with
content `{"source", "step", "records"}` so the step name survives a path rename.
Per-query chunk segments wait for a step-level unit argument.

Writing is opt-in: `run_collection(adapters, config, artifact_path=None)` keeps
B22's return-only behaviour when no path is given, so unit tests stay file-free.
`write_chunk` / `write_report` live in `chunks.py`; the collector calls them
after each `ok` step and once at the end. Skipped, failed and empty steps write
no chunk; the report is written even for a failed run (it is the evidence).
`run_report.json` is rewritten per run of a scope.

Use `files_io.save_data(..., with_timestamp=False)` until B30 supplies the atomic
write. Tests for the three Done-when cases go in the `tests/test_collector.py`
module created in B22.

See [implementation-flow.md](implementation-flow.md#b23--chunks-and-the-run-report)
and [design/artifacts.md](../../design/artifacts.md#resume-and-failure).

## Done when

- A skipped step has no chunk.
- A failed step is named in the report.
- Rerunning the same unit replaces its chunk, not duplicates it.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
