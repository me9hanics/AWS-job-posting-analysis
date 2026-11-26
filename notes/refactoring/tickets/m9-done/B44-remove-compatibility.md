# B44 — Remove compatibility code, dead code and stale traces

Status: todo · Milestone: M9 Done · Phase 9 · Size: L

- Depends on: B43
- Files: `scrapers/sites.py` shim, empty modules, `pipelines/collecting.py`,
  unused schedule scripts, any module/function/constant nothing calls,
  `processing/derive_profile_postings.py` and other shared modules

## Do

1. Remove re-exports with no named caller (Q16).
2. Archive or delete superseded entry points.
3. Keep one documented way to run collection, derivation and outputs.
4. Delete what nothing calls: modules, functions, constants, parameters and
   artifacts left from the old implementation. A deleted path is not a reason
   to keep its helpers "just in case".
5. Remove old *traces* from code that stays: a deleted or untracked feature must
   not survive as a default value, a hidden branch, a loose keyword argument or
   a filename. Use neutral constants or parameters instead of one profile's; a
   profile's rules live in `profiles/<name>.py` and its values in `conf/`
   (B32, B34).
   `processing/derive_profile_postings.py` is the example to clean: the
   `DANI_*` parameter defaults, the inline Vienna-penalty rule, the
   `migration_baseline_*.json` write, the `efficient_storing` extra artifact and
   the misspelled/vestigial parameters are Dani traces, not generic derivation.
   They came from a collect pipeline that is not tracked by Git; not being
   tracked is not a reason to keep them.

## Done when

- No module is imported only for compatibility.
- No duplicate scraper or empty placeholder remains.
- Every remaining module, function, constant and parameter has a caller; a
  symbol only a deleted path used is deleted.
- No shared module names a profile or carries that profile's constant, default,
  branch or artifact name. `derive_profile_postings` (or its B33 replacement)
  takes its rules from `ProfileConfig` and the profile module only.
- `basescraper.py` exposes no overridable helper and declares no `gather_data`
  template; no site module overrides a base method (Q30).
- The suite passes.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).
