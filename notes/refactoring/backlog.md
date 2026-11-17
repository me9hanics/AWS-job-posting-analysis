# Refactoring backlog

Status: ordered execution list, 2026-11-16. This is downstream of the
[plan](plan.md), [breakdown](breakdown/README.md) and [design](design/README.md).
It does not change any decision; it turns them into small, verifiable tasks.

IDs are stable (`B01` is task 1, `B46` is task 46). Use the ID in commit
messages and notes. Tick a task only when its "Done when" line is true.

## How to use

- Work top to bottom unless a task says it can run in parallel.
- Each task leaves the working tree runnable and the test suite green.
- If a task grows beyond one reviewable change, split it and add `Bxxa`/`Bxxb`
  rather than hiding the size.
- Do not start a task whose "Depends on" task is not done.
- When a task changes a design assumption, update the corresponding document in
  the same change; do not leave the backlog as the only source of truth.

## Order at a glance

| Phase | Tasks | Theme |
| --- | --- | --- |
| 0 | B01–B05 | Baseline, portability, characterization tests |
| 1 | B06–B10 | Data specs and the step contract |
| 2 | B11–B15 | Collapse duplicate scrapers |
| 3 | B16–B18 | Split HTTP and browser mechanics |
| 4 | B19–B25 | Multi-step adapters and the universal collector |
| 5 | B26–B31 | Pure data layer and unfiltered universal storage |
| 6 | B32–B35 | Profile configuration and generic derivation |
| 7 | B36–B39 | Stage orchestration, resume and failure artifacts |
| 8 | B40–B43 | Kedro composition (user-owned) |
| 9 | B44–B46 | Cleanup, documentation, final gates |

Critical path:

```text
B02 → B03 → B04 → B05 → B11 → B12 → B13 → B14 → B15 → B16 → B17 → B18
→ B19 → B20 → B21 → B22 → B23 → B24 → B25 → B26 → B27 → B28 → B29
→ B30 → B31 → B32 → B33 → B34 → B35 → B36 → B37 → B38 → B40 → B41
→ B42 → B43 → B44 → B46
```

B39 (backfill dry run) is optional and off the critical path. B06–B10 can run
in parallel with B03–B05 once B02 is done.

## Milestones

| Milestone | Tasks | Outcome |
| --- | --- | --- |
| M1 — Safe baseline | B01–B05 | Tests lock current data rules; paths are portable; site parsing has fixtures |
| M2 — Contracts | B06–B10 | Specs and the step shape exist, with no runtime change |
| M3 — One scraper per site | B11–B18 | No duplicate classes; HTTP and browser mechanics separated |
| M4 — Collector | B19–B25 | Multi-step adapters run through `run_collection`, with chunks and a report |
| M5 — Data layer | B26–B31 | Pure data functions; universal stores everything; writes are safe |
| M6 — Profiles | B32–B35 | Config plus functions; no profile import in derivation |
| M7 — Stages | B36–B39 | Startable stages, spec checks, resume and failure artifacts |
| M8 — Kedro | B40–B43 | Kedro reproduces the script path for collection and Dani |
| M9 — Done | B44–B46 | No compatibility shims, docs match, fresh-clone gate passes |

M1 and M2 are deliberately low-risk: apart from B03 (path resolution), they add
tests and contracts without changing scraping or derivation. Do not skip them to
reach the collector faster; the collector depends on both the fixtures and the
step contract.

## Verification commands

Run from the repository root:

```bash
uv run python -m unittest discover -s tests
```

Current baseline at the time of writing: 54 tests pass. Use a narrower file
while iterating, for example:

```bash
uv run python -m unittest tests.test_incremental_collection
```

A task that claims "no absolute path" is verified with:

```bash
rg "[A-Za-z]:[\\\\/]|/home/|/Users/" src tests
```

A task that claims "no duplicate scraper" is verified with:

```bash
rg "class BaseScraper|class KarriereAT|class Raiffeisen" src
```

## Phase 0 — Baseline, portability, characterization

### B01 — Record the baseline

- Depends on: —
- Size: S
- Files: `notes/refactoring/breakdown/migration.md`
- Do:
  1. Fill the baseline section with the live entry points, the importers of
     `scrapers.sites` and `collecting.get_postings`, the saved-data layout, and
     the current test command.
  2. Record every absolute path and where it comes from.
  3. Note which schedule scripts are archive-only.
- Done when:
  - the baseline section has no `TBD` and matches `rg` output;
  - the test command is written down;
  - archive-only scripts are named so they do not become gates.

### B02 — Confirm a clean test command and baseline result

- Depends on: B01
- Size: S
- Files: `notes/refactoring/backlog.md`, `notes/refactoring/breakdown/migration.md`
- Do:
  1. Run `uv run python -m unittest discover -s tests`.
  2. Record the number of tests and the command in the baseline.
  3. If a test needs the network, mark it and exclude it from the default gate.
- Done when:
  - the command passes from a clean `uv run` without manual `PYTHONPATH`;
  - the baseline names the command and the pass count.
- Note: at review time, 54 tests passed with this command.

### B03 — Remove the absolute repository root

- Depends on: B02
- Size: S
- Files: `src/jobscraping/config/configs.py`, `tests/`
- Do:
  1. Replace the hardcoded `REPO_ROOT_PATH` with a value derived from
     `__file__`, for example `Path(__file__).resolve().parents[3]`.
  2. Keep the derived absolute value only at runtime; do not commit a path.
  3. Add one test that asserts `<root>/pyproject.toml` exists. Do not assert on
     string formatting; the point is that the root resolves to the repository.
  4. Run the suite and an import from a different working directory.
- Done when:
  - a drive-letter or home-directory path pattern finds nothing in `src tests`;
  - the test suite passes;
  - `config` imports from a directory other than the repository root.
- Why first: every later path change is easier when the root is already
  relative and portable.

### B04 — Characterization tests for data rules

- Depends on: B02
- Size: M
- Files: `tests/test_data_rules.py` (new), `tests/fixtures/`
- Do:
  1. Lock current behaviour for `factual_postings`: profile keys are dropped,
     raw keys and unknown keys survive.
  2. Lock `merge_observations`: earliest `first_collected_on`, latest
     `last_collected_on`, recomputed `timespan_days`, latest non-empty
     description, idempotent second merge.
  3. Lock `get_added_and_removed` on identity sets and ordering; do not test the
     `points` side effect here, because B28 removes it.
  4. Add a deliberately broken-merge check locally to prove the tests fail.
- Done when:
  - the new tests pass on unchanged code;
  - a wrong date or description merge fails at least one test.

### B05 — Fixture pages and parser parity

- Depends on: B02, B03
- Size: M
- Files: `tests/fixtures/karriere/`, `tests/fixtures/raiffeisen/`, `tests/`
- Do:
  1. Capture one listing payload and one detail payload per site as small
     fixtures. Strip cookies, tokens and personal data.
  2. Test the extraction/parsing functions that do not require a live browser.
  3. If a parser is trapped inside a live `gather_data` call, record the seam
     needed for B12/B13 instead of forcing a network test.
- Done when:
  - at least one listing and one detail fixture per site parse to expected
    facts without network access;
  - the fixtures are small enough to review.

## Phase 1 — Data specs and the step contract

These tasks add contracts only; no runtime behaviour changes.

### B06 — Create the `specs` package

- Depends on: B02
- Size: S
- Files: `src/jobscraping/specs/__init__.py`, `src/jobscraping/specs/base.py`
- Do:
  1. Add frozen `FieldSpec` and `DataSpec` dataclasses from
     [design/specs.md](design/specs.md).
  2. Implement `DataSpec.extend()` and `DataSpec.check(records)`.
  3. `check` returns human-readable problems; it does not mutate or coerce.
  4. Keep the package a leaf: stdlib only.
- Done when:
  - `from jobscraping.specs.base import DataSpec, FieldSpec` works;
  - the package imports without `pipelines`, `scrapers` or `profiles`.

### B07 — Define the five posting specs

- Depends on: B06
- Size: S
- Files: `src/jobscraping/specs/postings.py`
- Do:
  1. Add `DISCOVERED_POSTINGS`, `COLLECTED_POSTINGS`, `UNIVERSAL_POSTINGS`,
     `SCORED_POSTINGS`, `SELECTED_POSTINGS`.
  2. Use the field names that exist in `RAW_POSTING_FIELDS`, `store_universal`
     and `derive_profile_postings`; do not invent a new vocabulary.
  3. Keep required fields minimal (identity and URL); move completeness to the
     quality gate.
  4. Keep profile fields out of `UNIVERSAL_POSTINGS`.
- Done when:
  - all five import;
  - the field sets match [design/specs.md](design/specs.md#specs-per-step);
  - no profile-only key appears in `UNIVERSAL_POSTINGS`.

### B08 — Test the spec contract

- Depends on: B06, B07
- Size: S
- Files: `tests/test_specs.py` (new)
- Do:
  1. Missing required field is reported with the field name.
  2. Unknown extra fields pass and are not removed.
  3. `extend` returns a new spec and leaves the original untouched.
  4. `check` does not mutate the input records.
- Done when:
  - the tests cover the four rules above and fail if `check` starts coercing.

### B09 — Define the adapter step contract

- Depends on: B06
- Size: S
- Files: `src/jobscraping/scrapers/steps.py`
- Do:
  1. Add a small frozen `Step` (`name`, `run`, optional `input_spec`,
     `output_spec`).
  2. Add a `SiteAdapter` protocol (`source`, ordered `steps`).
  3. Document that a step list may be plain `(name, callable)` pairs; the
     dataclass is a convenience, not a framework.
  4. Do not add required/optional flags, a registry base class or a validation
     hierarchy.
- Done when:
  - the module imports with no runtime use;
  - a one-step and a two-step adapter can both be described by the types.

### B10 — Prove the step contract with a fake adapter

- Depends on: B09
- Size: S
- Files: `tests/test_steps_contract.py` (new)
- Do:
  1. Define a fake one-step adapter and a fake two-step adapter in the test.
  2. Exercise order, skip-by-name, a raising step, and zero records with a
     test-local runner.
  3. Confirm the contract can express both site shapes without a collector.
- Done when:
  - the test passes and needs no network, browser or profile;
  - the collector task (B22) can copy the test's call shape.

## Phase 2 — Collapse duplicate scrapers

Do this before adding more sites. Every new site would otherwise multiply the
duplication.

### B11 — Choose the canonical scraper implementations

- Depends on: B05
- Size: M
- Files: `design/module-seams.md`, `scrapers/sites.py`,
  `scrapers/basescraper.py`, `scrapers/websites/*`
- Do:
  1. Compare the active `sites.py` classes with `basescraper.py` and the
     `websites/*` variants.
  2. Record which copy is canonical for `BaseScraper`, `KarriereAT` and
     `Raiffeisen`, and why.
  3. Run the B05 fixtures against the chosen copy.
- Done when:
  - the decision is written in `design/module-seams.md`;
  - the chosen copy passes the parser parity fixtures;
  - no third copy remains to “merge later”.

### B12 — Move `KarriereAT` to its site module

- Depends on: B11
- Size: M
- Files: `src/jobscraping/scrapers/websites/karriere_at.py`,
  `src/jobscraping/scrapers/sites.py`, `scrapers/__init__.py`
- Do:
  1. Move the canonical class body unchanged.
  2. Export it from `websites/__init__.py` and `scrapers/__init__.py`.
  3. Keep a temporary re-export from `sites.py` so existing imports work.
- Done when:
  - `KarriereAT` is defined in exactly one file;
  - fixture parsing is unchanged;
  - existing call sites still import successfully.

### B13 — Move `Raiffeisen` to its site module

- Depends on: B12
- Size: M
- Files: `src/jobscraping/scrapers/websites/raiffeisen.py`,
  `src/jobscraping/scrapers/sites.py`
- Do:
  1. Same move and parity check as B12.
  2. Keep the `sites.py` re-export until B15/B44.
- Done when:
  - `Raiffeisen` is defined in exactly one file;
  - fixture parsing is unchanged.

### B14 — Make `BaseScraper` single-source and shrink `sites.py`

- Depends on: B13
- Size: M
- Files: `src/jobscraping/scrapers/basescraper.py`,
  `src/jobscraping/scrapers/sites.py`, `scrapers/__init__.py`
- Do:
  1. Choose one `BaseScraper` body and delete the duplicate.
  2. `sites.py` becomes a compatibility re-export only, or is removed if no
     caller still needs it (Q16).
  3. Keep public names stable through `scrapers/__init__.py`.
- Done when:
  - `rg "class BaseScraper"` returns one match;
  - `rg "class KarriereAT|class Raiffeisen"` returns one match each;
  - the suite and fixture tests pass.

### B15 — Update every importer

- Depends on: B14
- Size: S
- Files: `pipelines/collecting.py`, `processing/postings_utils.py`,
  `script.py`, `schedule/emails.py`, `schedule/*_collect.py`
- Do:
  1. Replace `from jobscraping.scrapers import sites` with the public
     `BaseScraper`/site imports.
  2. Keep `schedule/hardverapro_collect.py` untouched (archive-only, Q17).
  3. Leave no import of a deleted module.
- Done when:
  - `rg "scrapers import sites|scrapers.sites"` finds only the intentional
    compatibility shim, if one still exists;
  - the suite passes.

## Phase 3 — Split HTTP and browser mechanics

Keep `scrape.py` as a facade while moving; remove it only when no caller needs
it.

### B16 — Extract the HTTP path

- Depends on: B15
- Size: M
- Files: `src/jobscraping/scrapers/http.py`, `src/jobscraping/scrapers/scrape.py`
- Do:
  1. Move the `requests`/response path into `http.py`.
  2. Keep public helper names re-exported from `scrape.py`.
  3. Add a fixture test for one request/parse path without network.
- Done when:
  - `http.py` imports no Selenium;
  - callers outside the scraper package are unchanged;
  - fixture tests pass.

### B17 — Extract the headless-browser path

- Depends on: B16
- Size: M
- Files: `src/jobscraping/scrapers/browser.py`, `scrapers/scrape.py`
- Do:
  1. Move Selenium session setup, popups and scrolling into `browser.py`.
  2. Keep the facade re-exports.
  3. Ensure no HTTP-only caller imports Selenium.
- Done when:
  - `browser.py` imports no `requests` request path;
  - scraper fixture tests pass;
  - importing `http.py` does not import Selenium.

### B18 — Extract pagination and retire the facade

- Depends on: B17
- Size: S
- Files: `src/jobscraping/scrapers/pagination.py`, `scrapers/scrape.py`
- Do:
  1. Move URL construction and next-page rules.
  2. Update internal imports to `http`/`browser`/`pagination`.
  3. Remove `scrape.py` if no caller outside the package needs it; otherwise
     keep a thin re-export and note the caller.
- Done when:
  - pagination tests pass;
  - `scrape.py` is either gone or contains only re-exports;
  - no site module contains HTTP/session code.

## Phase 4 — Multi-step adapters and the universal collector

### B19 — Give `KarriereAT` declared steps

- Depends on: B12, B16, B17, B18
- Size: M
- Files: `scrapers/websites/karriere_at.py`
- Do:
  1. Split the existing flow into two adapter functions, for example
     `listings` and `details`; use names that describe the site, not a global
     vocabulary.
  2. Expose `steps = (Step("listings", listings), Step("details", details))`.
  3. Keep the final facts identical to the pre-split flow.
  4. Keep `gather_data` as a compatibility wrapper until B24 wires the
     collector; the step list is the new path.
- Done when:
  - a listings-only run returns identity/URL records;
  - a full run returns the same facts as the B05 fixture baseline;
  - no required/optional flag is introduced;
  - the legacy entry point still calls the wrapper.

### B20 — Give `Raiffeisen` declared steps

- Depends on: B13, B19
- Size: M
- Files: `scrapers/websites/raiffeisen.py`
- Do:
  1. Same split as B19, using Raiffeisen's actual flow.
  2. Keep a single-step path if that is what the site actually does.
  3. Keep the legacy wrapper until B24.
- Done when:
  - the adapter exposes its steps in order;
  - fixture parity holds;
  - the two site modules do not share a hidden “main” step.

### B21 — Extract the quality gate

- Depends on: B15
- Size: S
- Files: `src/jobscraping/acquisition/quality.py`,
  `src/jobscraping/pipelines/collecting.py`
- Do:
  1. Move `validate_postings_quality` and its helpers into `acquisition/`.
  2. Keep a re-export in `collecting.py` until its callers move.
  3. Add tests for pass/fail cases with per-source thresholds.
- Done when:
  - the quality gate imports no profile module;
  - existing tests pass;
  - `collecting.py` is thinner by the moved functions.

### B22 — Create the universal collector

- Depends on: B09, B10, B19, B20, B21
- Size: L
- Files: `src/jobscraping/acquisition/collector.py`
- Do:
  1. Implement `run_collection(adapters, config)`.
  2. Iterate sites, queries and locations; run each adapter's steps in order;
     honor `CollectionConfig.steps`; merge by identity.
  3. Record step outcomes and errors in a run report structure.
  4. Do not store files here; return records plus the report.
- Done when:
  - a one-step and a two-step adapter both run;
  - skipping a step is observable;
  - zero records is a failure;
  - the collector imports no profile and no site module by name.

### B23 — Add chunk artifacts and the JSON run report

- Depends on: B22
- Size: M
- Files: `src/jobscraping/acquisition/chunks.py`,
  `src/jobscraping/acquisition/collector.py`
- Do:
  1. Write one chunk per completed site/query/location/step unit.
  2. Use the scope digest in the path; do not write an empty chunk for a failed
     unit.
  3. Write the JSON run report with unit, step, outcome and error.
  4. Leave atomic writes for B30; use the current save helper for now.
- Done when:
  - a skipped step has no chunk;
  - a failed step is named in the report;
  - rerunning the same unit replaces its chunk, not duplicates it.

### B24 — Wire the universal pipeline to the collector

- Depends on: B22, B23
- Size: M
- Files: `src/jobscraping/pipelines/scrape_universal.py`,
  `src/jobscraping/pipelines/collecting.py`
- Do:
  1. Replace the ad-hoc `scrape_sites` loop in the universal path with
     `run_collection`.
  2. Keep scope building, cache loading and storage in the pipeline for now.
  3. Leave the legacy `get_postings` path working.
- Done when:
  - the universal flow produces the same final facts as before;
  - the legacy profile scripts still pass their tests;
  - the pipeline contains no site-specific branch.

### B25 — Collector integration tests

- Depends on: B24
- Size: M
- Files: `tests/test_collector.py` (new)
- Do:
  1. One-shot adapter and two-step adapter through `run_collection`.
  2. Skip the detail step; assert partial records and the report.
  3. A step raises; assert the run continues where possible and names the error.
  4. Zero records; assert failure.
  5. Register a fake new site and prove no collector edit is needed.
- Done when:
  - all five cases pass;
  - the fake site is one module plus one registry entry.

## Phase 5 — Pure data layer and unfiltered storage

### B26 — Create `data/load.py`

- Depends on: B03
- Size: S
- Files: `src/jobscraping/data/load.py`, `src/jobscraping/pipelines/store_universal.py`
- Do:
  1. Move `load_postings` and the persistence wrapper into `data/load.py`.
  2. Keep `files_io` as the file-format layer; `data/load.py` owns paths and
     record loading.
  3. Update callers to use the data function.
- Done when:
  - `store_universal.py` no longer defines `load_postings`;
  - tests pass;
  - no absolute path is introduced.

### B27 — Move merge and history rebuild

- Depends on: B26, B04
- Size: M
- Files: `src/jobscraping/data/merge.py`,
  `src/jobscraping/pipelines/store_universal.py`
- Do:
  1. Move `merge_observations` and the history-rebuild logic.
  2. Keep the B04 fixtures as the parity gate.
  3. Make a second merge idempotent.
- Done when:
  - `data/merge.py` imports no pipeline module;
  - the B04 tests pass unchanged;
  - byte-identical JSON on a repeated fixture run.

### B28 — Make the diff neutral

- Depends on: B27
- Size: S
- Files: `src/jobscraping/data/compare.py`,
  `src/jobscraping/processing/postings_utils.py`
- Do:
  1. Move `get_added_and_removed` into `data/compare.py`.
  2. Remove the `points = 0` injection; profile derivation adds its own default.
  3. Add tests for added, removed and reappeared identities.
- Done when:
  - a universal diff contains no profile field;
  - a reappearing posting is current, not newly added;
  - the profile path still orders by points after derivation.

### B29 — Move generic enrichment and remove the scraper import

- Depends on: B27, B28
- Size: M
- Files: `src/jobscraping/data/enrich.py`,
  `src/jobscraping/processing/postings_utils.py`
- Do:
  1. Move `enrich_postings` and its re-processing behaviour into `data/enrich.py`.
  2. Remove the `BaseScraper` import from `processing/postings_utils.py`.
  3. Keep enrichment idempotent: rerun replaces derived values, never appends.
- Done when:
  - `rg "from jobscraping.scrapers" src/jobscraping/processing` finds nothing;
  - enrichment tests pass without a browser or network;
  - double enrichment is byte-stable.

### B30 — Atomic writes, UTC and `schema_version`

- Depends on: B26
- Size: M
- Files: `src/jobscraping/io/files_io.py`, `src/jobscraping/data/load.py`
- Do:
  1. Write to a temporary file in the destination directory and `os.replace`.
  2. Use UTC for new artifact timestamps and filenames.
  3. Add `schema_version` to vault artifacts.
  4. Keep reading legacy local-time files without conversion.
- Done when:
  - a simulated write failure leaves the previous file intact;
  - new timestamps are UTC;
  - every vault file has `schema_version`.
- Note: current artifacts are local-time; do not rewrite history in this task.

### B31 — Store every posting in universal

- Depends on: B22, B24, B27
- Size: M
- Files: `scrapers/basescraper.py`, `pipelines/scrape_universal.py`,
  `data/merge.py`, tests
- Do:
  1. Make the universal path stop running role/manager/relevance filtering;
     profiles own it.
  2. Keep the legacy profile path behaviour until its cutover; do not change
     `get_postings` in this task.
  3. Keep only factual normalization and quality gates on the universal path.
  4. Ensure a posting that a profile would reject still appears in universal.
- Done when:
  - a fixture with a manager/irrelevant title is stored in universal;
  - the same posting can be rejected by a profile;
  - the legacy profile tests still pass;
  - no profile field appears in universal records.

## Phase 6 — Profile configuration and generic derivation

### B32 — Add `ProfileConfig`

- Depends on: B07
- Size: M
- Files: `src/jobscraping/config/models.py`, `src/jobscraping/profiles/dani.py`
- Do:
  1. Add the frozen `ProfileConfig` from [design/specs.md](design/specs.md).
  2. Move Dani threshold, salary, locations, scoring and language values into
     the Dani config/defaults.
  3. Keep code behaviour unchanged.
- Done when:
  - `derive_profile_postings` can receive a `ProfileConfig`;
  - Dani values are no longer scattered defaults in the pipeline signature;
  - tests pass.

### B33 — Make derivation generic

- Depends on: B27, B28, B32
- Size: L
- Files: `src/jobscraping/processing/derive.py`,
  `src/jobscraping/processing/derive_profile_postings.py`
- Do:
  1. Move the generic derivation body into `processing/derive.py`.
  2. Accept `ProfileConfig` plus profile functions; remove Dani imports and
     defaults.
  3. Keep the existing delta rules and output ordering.
- Done when:
  - `processing/derive.py` imports no profile module;
  - Dani's selected output matches the baseline;
  - a second config can call the same function.

### B34 — Move profile rules and delete the empty modules

- Depends on: B33
- Size: M
- Files: `src/jobscraping/profiles/dani.py`,
  `processing/candidate_filtering.py`, `selection_filtering.py`, `scoring.py`
- Do:
  1. Keep candidate admission, role contributions, language assessment and
     title exclusions in the profile module.
  2. Put shared ranking/keyword mechanics in
     `processing/scoring_mechanics.py`.
  3. Delete the three empty modules.
- Done when:
  - the empty modules are gone;
  - `profiles/dani.py` imports no pipeline module;
  - candidate and selection behaviour are separately testable.

### B35 — Make profile current selected-only

- Depends on: B33, B34
- Size: S
- Files: `processing/derive.py`, tests
- Do:
  1. `current_postings.json` contains selected postings.
  2. `newly_added_postings.json` keeps the agreed delta semantics.
  3. Keep candidates in history.
- Done when:
  - a below-threshold candidate exists in history but not in current;
  - a known reappearance is not newly added;
  - the Dani test baseline is updated deliberately, not incidentally.

## Phase 7 — Stage orchestration, resume and failure artifacts

### B36 — Extract stage functions

- Depends on: B24, B33
- Size: L
- Files: `src/jobscraping/pipelines/collection.py`,
  `derivation.py`, `outputs.py`
- Do:
  1. Give each stage a named input, named output and explicit config.
  2. Keep the existing composite functions as thin sequences during migration.
  3. Remove file-format and profile details from pipeline modules.
- Done when:
  - every stage can run on fixtures without network;
  - the old entry points call the same stages;
  - no stage duplicates business logic.

### B37 — Add spec checks at stage boundaries

- Depends on: B36
- Size: M
- Files: stage modules, `specs/`
- Do:
  1. Check the input spec before work; report missing required fields.
  2. Check the output spec before writing.
  3. Allow unknown fields.
- Done when:
  - a stage started on data missing a required field fails before work;
  - a stage with extra fields succeeds and preserves them;
  - the error names the field.

### B38 — Resume, partial failure and incomplete-run artifact

- Depends on: B23, B36
- Size: M
- Files: `acquisition/chunks.py`, stage modules, `io/files_io.py`
- Do:
  1. Reuse valid chunks for the same scope digest.
  2. Write one `incomplete_run_<timestamp>.json` on a rejected quality gate.
  3. Leave the previous current/history untouched on failure.
- Done when:
  - interrupt and resume reproduce the same vault;
  - a failed gate leaves the prior snapshot intact and writes one artifact;
  - a skipped step remains visible as a missing chunk.

### B39 — Backfill dry run (optional, off critical path)

- Depends on: B30, B31
- Size: M
- Files: `analysis/` or a one-off script
- Do:
  1. Read existing profile histories.
  2. Report counts per profile, unique IDs, overlaps, conflict examples and
     fields that would be dropped.
  3. Do not write to the live vault.
- Done when:
  - a reviewable dry-run JSON exists;
  - no live file is modified;
  - Q14 remains a plan, not an executed migration.

## Phase 8 — Kedro composition (user-owned)

The user builds the Kedro graph. These tasks are the support work and the
parity checks; they do not prescribe node granularity.

### B40 — Add the Kedro skeleton

- Depends on: B36
- Size: M
- Files: `pyproject.toml`, `src/jobscraping/settings.py`,
  `src/jobscraping/pipeline_registry.py`, `conf/`
- Do:
  1. Add Kedro and the dataset extras actually used; regenerate `uv.lock`.
  2. Add `[tool.kedro]` pointing at the existing `src/` package.
  3. Add empty settings/registry modules and confirm `kedro run` starts.
- Done when:
  - `kedro run` can load an empty project;
  - no existing script path changes;
  - dependency versions are pinned in `uv.lock`.

### B41 — Add `conf/` parameters and a relative catalog

- Depends on: B40, B32
- Size: M
- Files: `conf/base/parameters.yml`, `parameters_profiles.yml`,
  `conf/base/catalog.yml`, `conf/<profile>/catalog.yml`
- Do:
  1. Map `CollectionConfig` and `ProfileConfig` values into YAML.
  2. Add catalog entries for existing artifacts with relative paths.
  3. Use per-profile overrides; no templating.
- Done when:
  - config objects load from `conf/`;
  - no absolute path appears in a tracked catalog;
  - a missing optional value falls back to code defaults.

### B42 — Build the collection pipeline

- Depends on: B41, B24
- Size: L
- Files: `pipelines/collection/`, user-owned
- Do:
  1. Wire the collection nodes the user chooses; start with collection plus
     storing rather than a universal pipeline.
  2. Keep step selection in `CollectionConfig`.
  3. Do not rely on Kedro caching for scraped data.
- Done when:
  - `kedro run --pipeline=collection` produces the same chunks/universal
    artifacts as the script path;
  - parameters come from `conf/`;
  - the run is restartable through chunks.

### B43 — Build derivation and outputs; parity check

- Depends on: B42, B36
- Size: L
- Files: `pipelines/derivation/`, `pipelines/outputs/`, user-owned
- Do:
  1. One parameterised derivation pipeline for every profile.
  2. Excel as a dataset; Markdown/email as side effects.
  3. Run the script path and Kedro path on the same inputs.
- Done when:
  - artifacts match byte-for-byte excluding timestamps;
  - `kedro run --pipeline=derivation --params=profile:dani` works;
  - no profile constants live in pipeline modules.

## Phase 9 — Cleanup and final gates

### B44 — Remove compatibility code and stale modules

- Depends on: B43
- Size: M
- Files: `scrapers/sites.py` shim, empty modules, `pipelines/collecting.py`,
  unused schedule scripts
- Do:
  1. Remove re-exports with no named caller (Q16).
  2. Archive or delete superseded entry points.
  3. Keep one documented way to run collection, derivation and outputs.
- Done when:
  - no module is imported only for compatibility;
  - no duplicate scraper or empty placeholder remains;
  - the suite passes.

### B45 — Update documentation and ADRs

- Depends on: B44
- Size: S
- Files: `README.md`, `GLOSSARY.md`, `docs/adr/`,
  `notes/refactoring/`
- Do:
  1. Update runtime docs to the new entry points.
  2. Add an ADR for the collection/profile boundary if the existing one no
     longer matches.
  3. Mark resolved backlog items and update design docs where behaviour changed.
- Done when:
  - a new contributor can run the project from the docs;
  - no document points at a retired module;
  - the backlog matches the tree.

### B46 — Final gates

- Depends on: B44, B45
- Size: S
- Files: all
- Do:
  1. Run the full suite.
  2. Run the import audit, duplicate-class audit and absolute-path audit.
  3. Clone into a fresh directory and run the documented command.
- Done when:
  - all tests pass;
  - no absolute path in `src`/`tests`;
  - one implementation per scraper class;
  - the fresh-clone run works without machine setup.
- This is the definition of done for the refactoring round, not for every
  future site or profile.

## New-site checklist

After B25, adding a site is a separate change and should use this checklist:

1. Add `src/jobscraping/scrapers/websites/<site>.py` with selectors, parsing and
   ordered steps.
2. Add one fixture payload per step to `tests/fixtures/<site>/`.
3. Register the adapter in `scrapers/websites/__init__.py` and the adapter
   registry used by the collector.
4. Add a collector test that runs the new adapter; do not edit the collector,
   data layer or a profile.
5. Run the suite.

If any step 1–4 requires a shared-code edit, stop and fix the seam before
adding the site.

## Deferred on purpose

- **Universal backfill into live data.** B39 is a dry run only; Q14 says plan,
  not execute.
- **Hardverapro.** Archive-only; do not fix its import as part of this
  refactoring (Q17).
- **New job sites.** The design must make them cheap, but adding one is not a
  refactoring task.
- **Universal Kedro pipeline.** Optional and later; start with collection plus
  storing (Q7).
- **Scoring class / `ProfilePolicy`.** Not planned; values plus functions (Q4,
  Q5).
- **Compatibility for old saved data.** Not required (Q27).

## Status notes

- B01/B02 are mostly satisfied by the 2026-11-16 review; confirm and tick.
- If a task reveals that a design decision is wrong, stop and change the
  decision first. The backlog follows the design, not the other way around.
