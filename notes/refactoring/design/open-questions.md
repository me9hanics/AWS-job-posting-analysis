# Decisions and open questions

Status: decisions resolved 2026-11-16, refined 2026-11-24 (Q29). One question
remains open (Q16). The resolved list records what was decided and which document
follows; the original option lists are no longer needed.

This file is the design decision log. When a decision changes, update the row
and the affected document in the same change.

## Agreed

| # | Decision | Source |
| --- | --- | --- |
| A1 | Collection is profile-neutral; profiles own relevance, scoring and selection. | [ADR 0001](../../../docs/adr/0001-collection-and-profile-ownership.md) |
| A2 | Two filters: candidate admission and final selection. | [process_map](../process_map.md), [pipeline discussion](../../../src/jobscraping/processing/README.md) |
| A3 | Dani is the first migrated profile. | [process_map](../process_map.md) |
| A4 | The refactoring moves behaviour before improving it. | [plan](../plan.md) |
| A5 | The topic keeps the document ladder and a Git-ignored raw archive. | User, 2026-11-16 |
| A6 | Data specs, one per step, are the stage contract: fields needed and produced. | User feedback, 2026-11-16 |
| A7 | Site adapters may expose multiple steps; steps can be skipped; failures produce partial results plus an alert. | User feedback, 2026-11-16 |
| A8 | A universal collector orchestrates adapters and owns the vault. | User feedback, 2026-11-16 |
| A9 | Collection and profile tunables live in `conf/` YAML; data specs stay in code. | User feedback, 2026-11-16 |
| A10 | Drop `ArtifactPaths`, `QualityPolicy`, `QualityReport`, `ScoringConfig` and `LanguagePolicy` as separate dataclasses. | User feedback, 2026-11-16 |
| A11 | Posting records stay dicts on export; dataclasses may model related data, and the existing schema is not enforced. | User feedback, 2026-11-16 |
| A12 | The refactoring adds `specs/`, `acquisition/` and `data/` as new modules; it does not keep everything under `pipelines/` and `processing/`. | User, 2026-11-16 |
| A13 | No absolute paths. The repository root is derived from `__file__`; configured paths are relative to it. | User, 2026-11-16 |
| A14 | More job sites are coming soon. Adding one must be one adapter module plus registration, with no core edits. | User, 2026-11-16 |
| A15 | Universal collection stores all postings. Role, manager and relevance filtering happens in profiles. | User, 2026-11-16 |

## Resolved questions

| # | Decision | Consequence |
| --- | --- | --- |
| Q1 | Add all three modules: `specs/`, `acquisition/`, `data/`. | Target tree in [module-seams.md](module-seams.md#target-package-map); plan Phase 1–2. |
| Q2 | Separate HTTP scraping from headless-browser scraping. | `scrapers/http.py` and `scrapers/browser.py` behind `scrape.py` during migration; pagination stays shared. |
| Q3 | Specs follow current pipeline logic: `DISCOVERED`, `COLLECTED`, `UNIVERSAL`, `SCORED`, `SELECTED`. Required fields are minimal; completeness is a quality-gate setting. | Field sets in [specs.md](specs.md#specs-per-step). |
| Q4 | No scoring class. Values live in `ProfileConfig.scoring`. | [specs.md](specs.md#profileconfig); [breakdown/profiles.md](../breakdown/profiles.md). |
| Q5 | No `ProfilePolicy` wrapper. Plain functions plus `ProfileConfig`. | Derivation takes config and callables; [breakdown/profiles.md](../breakdown/profiles.md). |
| Q6 | `conf/` holds anything a user may tune. Site constants such as CSS selectors stay in the adapter file. Specs stay in code. | [kedro-project.md](kedro-project.md#parameters-vs-code). |
| Q7 | Kedro is implemented by the user. Collection starts as one or more nodes with storing and other nodes, in the style of the current `_collect` pipelines; a universal pipeline is optional and later. | [kedro-project.md](kedro-project.md#pipelines-and-flows). |
| Q8 | One parameterised derivation pipeline, not one pipeline per profile. | `kedro run --pipeline=derivation --params=profile:<name>`. |
| Q9 | Per-profile catalog overrides now (`conf/<profile>/catalog.yml`). | No catalog templating. |
| Q10 | Excel as a Kedro dataset; Markdown and email as side effects for now. Preliminary. | [kedro-project.md](kedro-project.md#catalog). |
| Q11 | Chunks per site/query/location/step. Steps are declared in the adapter module, in order; `Step` may exist as a convenience, without enforcement machinery. No mandated `discover`/`describe` names. | [collection-steps.md](collection-steps.md). |
| Q12 | Atomic writes: temporary file in the same directory plus `os.replace`. | [artifacts.md](artifacts.md#resume-and-failure). |
| Q13 | UTC timestamps; a `schema_version` field on vault artifacts. | [artifacts.md](artifacts.md#resume-and-failure). |
| Q14 | Drop old profile points and provenance from universal records. Plan only; not executed in this round. | Universal specs in [specs.md](specs.md#specs-per-step). |
| Q15 | Delete `candidate_filtering.py`, `selection_filtering.py` and `scoring.py`; their roles live in `processing/` and `profiles/<name>.py`. | [breakdown/profiles.md](../breakdown/profiles.md). |
| Q16 | Open. Compatibility layer for `scrapers.sites` and `collecting.get_postings`. | See [Still open](#still-open). |
| Q17 | Hardverapro is archive-only. Its broken import may stay until cleanup and is not a migration gate. | [breakdown/migration.md](../breakdown/migration.md). |
| Q18 | Side outputs are not pipeline datasets. They are exports or BI views derived from records when needed. | [collection-steps.md](collection-steps.md#side-outputs). |
| Q19 | Universal stores every posting. Profiles do the filtering. A profile `current_postings.json` contains selected postings only. | [breakdown/data.md](../breakdown/data.md); [breakdown/profiles.md](../breakdown/profiles.md). |
| Q20 | Specs live in `src/jobscraping/specs/` as code and are passed to stages explicitly. They do not belong in `conf/`. Export column selections are config. | [specs.md](specs.md#where-specs-live). |
| Q21 | "Spec" means a data shape only. Configuration objects are `CollectionConfig` and `ProfileConfig`. | [specs.md](specs.md#specs-versus-configs). |
| Q22 | A step returns a new records dict; the caller rebinds (`records = step.run(records, config)`). | [collection-steps.md](collection-steps.md#execution-rules). |
| Q23 | Minimum viable run: the configured steps run without error. No per-adapter required-step declarations. Zero records is a failure. | [collection-steps.md](collection-steps.md#execution-rules). |
| Q24 | Overwrite `current_postings.json` after a successful profile run. No per-unit gating for now. | [artifacts.md](artifacts.md#collection-steps-and-partial-results). |
| Q25 | JSON run report now; revisit the shape with Kedro. | [artifacts.md](artifacts.md#stage-interface). |
| Q26 | Collector at `acquisition/collector.py`, entry point `run_collection`. | [module-seams.md](module-seams.md#target-package-map). |
| Q27 | No spec version or digest, and no compatibility requirement for old data. `schema_version` on the vault is enough. | [artifacts.md](artifacts.md#resume-and-failure). |
| Q28 | The universal history is expected but not guaranteed. Collection may be planned per pipeline and run as today; a profile's input is whatever records it is given, not "the universal vault". Interfaces that read or write universal data take records or paths as arguments; nothing may depend on one universal history existing. | [artifacts.md](artifacts.md#stage-interface), [open-questions.md](#universal-history-is-not-guaranteed). |
| Q29 | The universal record carries profile-neutral annotations: `language`, `guessed_required_languages` and `matched_titlewords`. Policy fields (`points`, `keywords`, `role_families`, `language_adjustment`, `language_excluded`, `profile_excluded`) stay in scored/selected. `data/enrich.py` produces the two language fields; derivation consumes them instead of recomputing. | [specs.md](specs.md#profile-neutral-annotations); backlog B07a, B29, B31, B33. |
| Q30 | A site is a class in its own module and is its own adapter. `BaseScraper` keeps only per-run setup (config normalization, dates), `source` and the declared `steps`; overridable helper methods are removed. Shared mechanics are module functions (`http`, `browser`, `pagination`, `parsing`); per-site differences are arguments or `rules` keys. Steps are declared by the site class, typically as bound methods in `__init__`. | [module-seams.md](module-seams.md#site-class-and-its-base); backlog B19, B20, B31, B44. |

## Still open

### Q16 Compatibility layer

`scrapers.sites` and `collecting.get_postings` may need a compatibility window
while their callers move. Decide when the first caller moves, not before. The
default remains: a re-export or wrapper only while a named caller exists; remove
it when that caller is converted. Nothing in the target design depends on the
answer.

## Constraints that shape the design

### No absolute paths

A repository root must be derived at runtime in one place, for example from the
config module:

```python
# src/jobscraping/config/paths.py
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]  # repo root, not src/
```

Every configured path is relative to that root. `config/configs.py` currently
hardcodes an absolute Windows repository root (`REPO_ROOT_PATH`);
removing it is part of the migration. Kedro catalog entries and `conf/` use
relative paths; `conf/local/` is only for machine-specific overrides and must
not be committed. Tests and fixtures use relative paths or `tmp_path`.

### More sites are coming

Adding a site should touch one adapter module plus one registration entry. It
must not require editing the collector, the data layer or a profile. That is why
the adapter owns its parsing and step list, while the collector owns only the
loop, merging and gates. The current cost of adding a site (copying a
`BaseScraper` variant) is the thing the refactoring removes.

### Universal data is unfiltered

The universal vault keeps every posting the configured queries returned,
including roles a profile will later reject. Profile filters run only after the
universal record exists. This is a change from the legacy profile pipeline,
which filters before storing.

### Universal history is not guaranteed

The universal history is the expected default, not a requirement. Collection may
be planned per pipeline and run the way it is today, so there may be one history,
several, or a pipeline that only produces chunks. Nothing in the implementation
may assume that "the universal vault" exists or is current:

- a profile filter receives records; it must not read a universal file, import a
  universal loader, or know where the input came from;
- stages that read universal artifacts take a path (or records) from the
  pipeline/catalog, never a module-level constant;
- a missing universal history is an ordinary input, not an error to work around.

In practice the universal history will exist and be used; making it a
convention rather than a dependency keeps a second collection layout possible
without a code change (Q28).

## How to change a decision

Record:

```text
Q<number>: <new decision>
Date:
Consequences: <what code or docs change>
```

Then update the row here, the affected design or breakdown document, and the
decision log in [README.md](../README.md#decision-log).
