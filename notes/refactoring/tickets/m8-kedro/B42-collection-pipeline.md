# B42 — Build the collection pipeline

Status: todo · Milestone: M8 Kedro · Phase 8 · Size: L · User-owned

- Depends on: B41, B24
- Files: `pipelines/collection/`, user-owned

## Do

1. Wire the collection nodes the user chooses; start with collection plus
   storing rather than a universal pipeline.
2. Keep step selection in `CollectionConfig`.
3. Do not rely on Kedro caching for scraped data.

## Done when

- `kedro run --pipeline=collection` produces the same chunks/universal artifacts
  as the script path.
- Parameters come from `conf/`.
- The run is restartable through chunks.
