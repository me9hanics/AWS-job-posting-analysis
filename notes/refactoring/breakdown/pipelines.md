# Pipelines workstream

Status: decided direction 2026-11-16. Stages exist as functions inside two mixed
modules; Kedro is not installed. The Kedro graph is built by the user, starting
with collection and storing.

Owns composition: which stages run, in what order, with which artifacts, and how
a failure is reported. It does not own business rules.

## Current state

- `pipelines/scrape_universal.py` composes scope building, cache loading,
  scraping, quality validation and storage in one function. It is the current
  universal collector, but it also owns caching and storage details and has no
  notion of selectable site steps.
- `pipelines/derive_profile_postings.py` composes history loading, candidate
  filtering, language analysis, scoring, delta comparison, history merge,
  storage, selection and a company summary in one function. It also performs
  migration-baseline bookkeeping and optional timestamped dumps.
- `pipelines/store_universal.py` mixes persistence with merge logic.
- `pipelines/dani.py` is a two-line glue function.
- `pipelines/collecting.py` remains the legacy profile pipeline and the source
  of shared acquisition helpers.
- `pipelines/cli.py` provides argparse collection arguments; `schedule/*.py`
  scripts call the pipeline functions directly.
- The intended stage names are recorded in
  [the pipeline discussion](../../../src/jobscraping/processing/README.md):
  `scrape_universal`, `generic_enrich_universal`, `store_universal`,
  `candidate_filter_profile`, `score_profile`, `selection_filter_profile`,
  `outputs_profile`. The current code does not follow that decomposition.

## Target

A stage is a function with named inputs, named outputs and a defined failure
behaviour. Orchestration only wires stages; it contains no filtering, scoring or
file-format logic.

```text
pipelines/
  stages/          # or acquisition/ + data/ + profiles/ if that split wins
  flows/           # flow definitions; later Kedro pipelines
  cli.py           # thin local entry point
```

Stage contract table (proposal):

| Stage | Input | Output | Failure |
| --- | --- | --- | --- |
| `collect_universal` | `CollectionConfig` (YAML), adapter registry, optional cache seed | shared records, chunks, scope digest, JSON run report | failed step recorded and run continues; zero records → acquisition failure |
| `enrich_generic` | raw facts | raw facts with derived generic fields | per-record errors recorded, stage continues |
| `store_universal` | enriched facts, scope digest | current, history, newly added | write conflict aborts before replacement |
| `derive_profile` | input records from the caller, `ProfileConfig`, profile functions, previous history | candidates, scored history, selected | policy error aborts with profile named |
| `generate_outputs` | selected artifacts, output config | Excel, Markdown, email | missing optional output is skipped, not fatal |

Each stage must be runnable alone from saved artifacts (the "startable" goal).
It checks its input data spec first and reports missing required fields before
doing work. See [specs.md](../design/specs.md).

## Changes

1. Extract stage functions from `scrape_universal.py` and
   `derive_profile_postings.py`; keep the current composite functions as thin
   sequences of stage calls during migration.
2. Name and isolate the universal collector: adapters, query units, step
   selection, merge, quality gates and chunk writes. Move site-agnostic looping
   out of `scrape_universal.py` and `collecting.py`.
3. Move persistence out of `store_universal`'s pure parts (see
   [data.md](data.md)).
4. Build `CollectionConfig` and `ProfileConfig` from `conf/` YAML at the
   pipeline boundary. Stage functions should receive config objects, not
   scattered defaults.
5. Add explicit failure artifacts and a "do not replace on failure" rule for
   every writing stage. A partial collection writes what succeeded and reports
   what did not.
6. Make the scope digest the resume key: the same scope may reuse chunks, a
   different scope must not silently overwrite the vault.
7. Add spec checks at stage entry and exit (see [specs.md](../design/specs.md)).
8. Add resume: read existing chunks for the same scope, skip completed units,
   record partial units.
9. Keep stage functions stable for the user's Kedro work: `conf/`, catalog,
   parameters, `settings.py`, `pipeline_registry.py`, node wrappers. Start with
   collection and storing; the graph may use several nodes and later replace
   some `_collect` scripts. Follow [kedro-project.md](../design/kedro-project.md).
10. Retire `schedule/*_collect.py` and `pipelines/cli.py` duplication once Kedro
    runs the same stages. Keep one documented way to run.
11. Replace the absolute `REPO_ROOT_PATH` with a root derived from `__file__`,
    and keep every catalog/config path relative.

## Dependencies

- Collection and Data workstreams must expose stable functions first.
- Profile config and profile-function contract for `derive_profile`.
- Outputs workstream for the final stage.

## Completion check

- Every stage can be called on fixtures without a network connection.
- One single-shot adapter and one multi-step adapter both run through the
  universal collector.
- A skipped step yields a partial result that the next stage accepts or rejects
  explicitly.
- Interrupting a collection and rerunning produces the same vault.
- A failed quality gate leaves the previous current/history files untouched.
- Starting a stage on data that lacks a required field fails before the stage
  runs, with the field named.
- `kedro run` reproduces the script path's artifacts byte-for-byte (excluding
  timestamps).
- No pipeline module contains profile constants, score formulas or file-format
  details.
- No pipeline module or catalog contains an absolute path.

## Decided points

- One parameterised derivation pipeline (Q8).
- Scraping runs as Kedro node(s); initial scope is collection plus storing, not
  a universal pipeline (Q7).
- Excel as a dataset; Markdown/email as side effects (Q10).
- JSON run report now (Q25).

The only open design question is Q16, the compatibility layer. See
[open-questions.md](../design/open-questions.md#still-open).

## Design references

- [Collection steps](../design/collection-steps.md)
- [Kedro project](../design/kedro-project.md)
- [Specs and dataclasses](../design/specs.md)
- [Artifacts](../design/artifacts.md)
- [Module seams](../design/module-seams.md)
