# B40 — Add the Kedro skeleton

Status: todo · Milestone: M8 Kedro · Phase 8 · Size: M · User-owned

- Depends on: B36
- Files: `pyproject.toml`, `src/jobscraping/settings.py`,
  `src/jobscraping/pipeline_registry.py`, `conf/`

## Do

1. Add Kedro and the dataset extras actually used; regenerate `uv.lock`.
2. Add `[tool.kedro]` pointing at the existing `src/` package.
3. Add empty settings/registry modules and confirm `kedro run` starts.

## Done when

- `kedro run` can load an empty project.
- No existing script path changes.
- Dependency versions are pinned in `uv.lock`.
