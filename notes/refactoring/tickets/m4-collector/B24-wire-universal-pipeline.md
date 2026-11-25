# B24 — Wire the universal pipeline to the collector

Status: todo · Milestone: M4 Collector · Phase 4 · Size: M

- Depends on: B22, B23
- Files: `src/jobscraping/pipelines/scrape_universal.py`,
  `src/jobscraping/pipelines/collecting.py`

## Do

1. Replace the ad-hoc `scrape_sites` loop in the universal path with
   `run_collection`.
2. Keep scope building, cache loading and storage in the pipeline for now.
3. Leave the legacy `get_postings` path working.

## Implementation notes

Extract the constructor mapping from `scrape_sites` into a `build_scraper`
helper and use it from both `scrape_sites` (behaviour unchanged) and the
universal flow. The universal flow then builds one `CollectionConfig` with the
cache as a config input, calls `run_collection(adapters, config,
artifact_path=path)`, and keeps everything else where it is.

Order matters for failure behaviour: after `run_collection`, `factual_postings`,
then — if `report["failed"]` — raise before the quality gate and before
`store_universal_postings`, so `current_postings.json` and
`postings_history.json` stay byte-identical. The raised message embeds each
failed step's recorded error verbatim, which keeps the existing "HTTP 410"
expectation valid. The collector itself never raises for a step error.

Keep the existing scope dict passed to `store_universal_postings` unchanged so
`collection_scope.json`, `same_scope` and the retention baseline do not shift on
the switch. `pipelines/dani.py` needs no edit; `collect_dani_postings` keeps
forwarding cache and quality arguments through `**kwargs`.

The WIP `tests/test_raw_collection.py` fake sources implement only
`gather_data`; convert those four flow cases to one-step adapters in this
ticket. Do not add a step-less compatibility branch to the pipeline. The legacy
`get_postings` / `scrape_sites` path and both `gather_data` wrappers stay.

See [implementation-flow.md](implementation-flow.md#b24--the-universal-pipeline-uses-the-collector).

## Done when

- The universal flow produces the same final facts as before.
- The legacy profile scripts still pass their tests.
- The pipeline contains no site-specific branch.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
