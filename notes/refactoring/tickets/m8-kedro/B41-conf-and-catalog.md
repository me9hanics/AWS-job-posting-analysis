# B41 — Add `conf/` parameters and a relative catalog

Status: todo · Milestone: M8 Kedro · Phase 8 · Size: M · User-owned

- Depends on: B40, B32
- Files: `conf/base/parameters.yml`, `parameters_profiles.yml`,
  `conf/base/catalog.yml`, `conf/<profile>/catalog.yml`

## Do

1. Map `CollectionConfig` and `ProfileConfig` values into YAML.
2. Add catalog entries for existing artifacts with relative paths.
3. Use per-profile overrides; no templating.

## Done when

- Config objects load from `conf/`.
- No absolute path appears in a tracked catalog.
- A missing optional value falls back to code defaults.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
