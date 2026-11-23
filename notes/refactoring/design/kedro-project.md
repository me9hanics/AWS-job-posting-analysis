# Kedro project

Status: requested direction; implementation owned by the user (2026-11-16).
Kedro is not installed and no `conf/` exists. This document records constraints
and a possible layout; it is not a mandated node graph.

Kedro becomes the composition and configuration layer: pipelines define which
stages run, `conf/` defines their parameters and artifact paths, and the package
keeps the actual logic. It is not a fourth copy of the business rules.

The user will build the Kedro project. Initial scope: collection as one or more
nodes, plus storing and other stages, in the style of the current `_collect`
files and pipelines. A universal pipeline is optional and can come later. The
first goal is to see how Kedro behaves, not to land the final graph.

## Feasibility (checked 2026-11-16)

- `pyproject.toml` requires Python `>=3.13.17`.
- PyPI metadata: `kedro` 1.8.0 requires `>=3.10` and declares 3.13/3.14
  classifiers; `kedro-datasets` 10.0.0 requires `>=3.10`. So the requested
  setup is feasible on the current interpreter.
- Exact dataset extras and class paths must be confirmed against the installed
  version in Phase 5; do not copy them from an older tutorial.

## Layout

Retrofit the existing `src/jobscraping` package instead of generating a new
project and moving code twice.

```text
pyproject.toml                 # + [tool.kedro]
conf/
  base/
    catalog.yml
    parameters.yml             # acquisition, quality, output defaults
    parameters_profiles.yml    # per-profile tuning
    globals.yml                # shared path prefixes, profile names
  local/                       # machine paths, credentials, overrides (ignored)
src/jobscraping/
  settings.py                  # project settings and hooks
  pipeline_registry.py         # register_pipelines()
  pipelines/
    collection/
      nodes.py
      pipeline.py
    derivation/
      nodes.py
      pipeline.py
    outputs/
      nodes.py
      pipeline.py
```

`pyproject.toml` gains a project section Kedro uses to locate the package:

```toml
[tool.kedro]
package_name = "jobscraping"
project_name = "jobscraping"
source_dir = "src"
```

The existing `[tool.setuptools.packages.find] where = ["src"]` already matches
the `src/` layout. Add `kedro` and the `kedro-datasets` extras for the dataset
types actually used, then regenerate `uv.lock`.

## Pipelines and flows

A possible set of pipelines:

| Pipeline | Stages | Purpose |
| --- | --- | --- |
| `collection` | build `CollectionConfig` → load cache → collection (one or more nodes) → validate quality → store universal | one acquisition run |
| `derivation` | load universal → candidate filter → score → language assess → diff → merge history → select → store profile | one profile run; one parameterised pipeline for every profile |
| `outputs` | prepare rows → render Excel → render Markdown → optional email | regenerate deliverables |
| `__default__` | optional; wire whatever the user wants end to end | end-to-end run |

The collection pipeline may be sliced into several nodes. One monolithic
`collect_universal` node is an option, not a requirement: slicing by stage
(`load cache`, `collect`, `validate`, `store`) mirrors the current `_collect`
scripts and may replace some of them. Slicing by adapter/step is also possible
but multiplies nodes per site, which matters with more sites coming. Pick node
granularity in the Kedro work, not here.

Node mapping from current code:

| Node | Current function |
| --- | --- |
| `build_collection_config` | inline scope building in `run_universal_scrape_flow` |
| `load_cache` | `load_postings`, `factual_postings` |
| `collect` | `scrape_sites` plus adapter step selection; may be split further |
| `validate_quality` | `validate_postings_quality` |
| `store_universal` | `store_universal_postings` |
| `load_universal` | catalog dataset, no node |
| `candidate_filter` | filter inside `derive_profile_postings` |
| `score` | `rank_postings`, `find_keywords_in_postings`, `guess_required_languages` |
| `assess_language` | `assess_language` + `language_adjustment` |
| `diff_history` | `get_added_and_removed` |
| `merge_history` | `merge_observations` |
| `select` | `select` closure in `derive_profile_postings` |
| `store_profile` | `files_io.save_data` calls |
| `generate_outputs` | `outputs.generate_outputs`, `log_to_markdown`, `send_email` |

A node should call a stage function; it should not contain the logic. That is
why [Phase 4](../plan.md#phase-4-stage-orchestration-and-artifacts) precedes
Kedro adoption.

Step selection is a parameter (`CollectionConfig.steps`). Whether the loop over
adapters and steps stays inside one node or is expressed as several nodes is the
user's implementation choice; the collector contract in
[collection-steps.md](collection-steps.md) does not depend on it.

## Catalog

Proposal; names are the interface between nodes and `conf/`:

| Dataset | Type (proposal) | Path | Layer |
| --- | --- | --- | --- |
| `raw_chunks` | `partitions.PartitionedDataset` | `data/save/postings/universal/chunks/` | bronze |
| `companies` | not a dataset | export or BI view when needed | — |
| `run_report` | `json.JSONDataset` (future) | `data/save/postings/universal/run_report.json` | bronze |
| `universal_current` | `json.JSONDataset` | `data/save/postings/universal/current_postings.json` | silver |
| `universal_history` | `json.JSONDataset` | `data/save/postings/universal/postings_history.json` | silver |
| `universal_added` | `json.JSONDataset` | `data/save/postings/universal/newly_added_postings.json` | silver |
| `universal_scope` | `json.JSONDataset` | `data/save/postings/universal/collection_scope.json` | silver |
| `profile_history` | `json.JSONDataset` | `data/save/postings/<profile>/postings_history.json` | gold |
| `profile_candidates` | `MemoryDataset` or JSON | not persisted by default | gold |
| `profile_current` | `json.JSONDataset` | `data/save/postings/<profile>/current_postings.json` | gold |
| `profile_added` | `json.JSONDataset` | `data/save/postings/<profile>/newly_added_postings.json` | gold |
| `excel_report` | `pandas.ExcelDataset` or side effect | `data/save/excels/...` | output |

Placeholder handling: per-profile overrides now (`conf/<profile>/catalog.yml`
overriding the `profile_*` paths). Do not invent catalog templating. All catalog
paths are relative; never put an absolute local path in a tracked catalog file.
`conf/local/` holds machine-specific values only and is not committed.

Excel is a dataset (`pandas.ExcelDataset` or the installed equivalent). Markdown
and email remain side effects for now; revisiting that is a later decision (Q10).

## Parameters vs code

| Value | Owner |
| --- | --- |
| Sites, queries, locations, enabled steps, cache mode, overrides | `conf/base/parameters.yml` → `CollectionConfig` |
| Quality thresholds and required fields per source | `conf/base/parameters.yml` |
| Profile threshold, salary floor, locations, scoring values, language values, output options | `conf/base/parameters_profiles.yml` → `ProfileConfig` |
| Export column selection | `conf/` (profile output options) |
| Data spec field names and requiredness | `specs/postings.py` (code) |
| Site selectors, URL patterns, parsing rules | the site's adapter module (code) |
| Profile behavior (candidate rule, role functions, language assessment) | `profiles/<name>.py` (code) |
| Filenames, column layout, request timeouts | `config/constants.py` (code) |
| Repository root | derived from `__file__` (code), never a config value |
| Credentials, local overrides | `conf/local/` (not committed) |

Rule: if changing the value is a normal operation, it belongs in `conf/`; if
changing it is a code review, it stays in code. Site selectors stay with the site
because they are implementation detail, not operations input (Q6). `config/configs.py`
currently holds both kinds, including the absolute `REPO_ROOT_PATH`; replace
that first with a root derived from `__file__`, then split when the catalog
lands. Keep one loader so there is never a second source of truth. A data spec is
code because processing depends on the field names; a query list is YAML because
changing it is an operation.

## Scraping inside or outside Kedro

Decided direction (Q7): scraping is a Kedro node (or several nodes) in the
collection pipeline. The user will implement it and start without a universal
pipeline, using collection plus storing and other nodes, in the style of the
current `_collect` files. Some of those files or pipelines may be replaced.

Implications to keep in mind:

- Kedro does not provide resume. Chunks and the scope digest still have to make
  a restart cheap, whether the scrape runs inside a node or from a command.
- A network-bound node is not deterministic. Do not rely on Kedro caching for
  scraped data; write chunks deliberately and treat the node as restartable.
- If a later design prefers an external scrape command writing chunks, the
  collector contract does not change. Only the entry point does.

The design does not require one particular placement; it requires that chunks,
the scope digest and the run report exist.

## Commands

```bash
kedro run --pipeline=collection
kedro run --pipeline=derivation --params=profile:dani
kedro run --pipeline=outputs --params=profile:dani
kedro run --pipeline=__default__ --params=profile:dani
kedro catalog list
kedro registry list
kedro viz
```

Exact flags and dataset class paths must be verified against the installed
version; the pipeline names are the stable part of this design.

## Migration path

1. Finish Phase 4: stages callable with explicit inputs/outputs and data specs.
2. Add `[tool.kedro]`, `settings.py`, `pipeline_registry.py`, empty pipelines.
3. Add catalog entries for existing artifacts without moving files.
4. Load `CollectionConfig` and `ProfileConfig` from `conf/`; wrap stages as
   nodes; keep `schedule/*.py` calling the same stage functions.
5. Switch one profile (Dani) to `kedro run`; compare artifacts.
6. Add the default pipeline and outputs; then retire duplicate entry points.
7. Move tunable values from `config/` to `conf/` last, when the catalog is
   proven.

## Risks

- **Two configuration systems.** `config/configs.py` and `conf/` coexist during
  migration. Mitigation: one loader, one documented owner per value, and the
  split in [parameters vs code](#parameters-vs-code).
- **Kedro for its own sake.** If nodes are thin wrappers over a tangle, YAML
  only hides it. Mitigation: Phase 4 first.
- **Resume confusion.** Kedro does not resume a half-finished scrape. Mitigation:
  chunk artifacts plus the scope digest, documented in
  [artifacts.md](artifacts.md).
- **Packaging drift.** `[tool.kedro]`, setuptools `src` layout and `uv.lock`
  must agree; verify `kedro run` from a clean environment, not only from the
  existing `.venv`.
- **Editor/tooling friction.** `kedro viz` and project metadata add files;
  decide whether they are tracked before generating them.

## Decisions already made

- Scraping runs as Kedro node(s); start without a universal pipeline (Q7).
- One parameterised derivation pipeline (Q8).
- Per-profile catalog overrides (Q9).
- Excel as a dataset; Markdown/email as side effects (Q10).
- `conf/` owns user-tunable values; site selectors and specs stay in code (Q6).

Remaining choices are implementation details inside the Kedro work. The only
open design question is Q16, the compatibility layer. See
[open-questions.md](open-questions.md).
