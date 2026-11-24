# Refactoring

Status: decisions recorded, 2026-11-16. No runtime restructuring is underway.
The live path is still `schedule/*_collect.py` →
`pipelines.collecting.get_postings`. The separated collection → derivation path
is wired for Dani only.

This topic holds the refactoring work: what we want, why, in what order, and the
raw material it came from. The documents form a ladder. Start at the top and
descend only as far as the question requires.

| Level | Document | Purpose |
| --- | --- | --- |
| 1 | [Plan](plan.md) | Goals, principles, phases, risks, success criteria. |
| 2 | [Breakdown](breakdown/README.md) | One document per workstream: current state, target, changes, dependencies. |
| 2.5 | [Backlog](backlog.md) | Ordered tasks B01–B46 with dependencies, files and done criteria. |
| 2.6 | [Tickets](tickets/README.md) | The same tasks as one ticket per file, grouped by milestone, with status and one `implementation-flow.md` per milestone. |
| 3 | [Design](design/README.md) | Concrete module maps, data specs, artifact contracts, and cross-block implementation-flow sketches. |
| — | [Process map](process_map.md) | The detailed 2026-11-02 work-and-dependency map. Still the long-form sequencing reference. |
| raw | [Raw archive](raw/restructuring-2026-11-02/README.md) | Historical plans and sketches. Local only, Git-ignored. |

## Reading the ladder

- **Changing direction or scope** → edit [plan.md](plan.md).
- **Adding or reordering work** → edit the relevant breakdown document and, if
  the dependency order changes, [process_map.md](process_map.md). The executable
  order is [backlog.md](backlog.md).
- **Starting a work session** → read the milestone's
  `implementation-flow.md` for the ordered per-ticket mocks, then pick the first
  unchecked task in [backlog.md](backlog.md) whose dependencies are done, and
  work it from its ticket in [tickets/](tickets/README.md).
- **Deciding a concrete interface** → edit the design document and remove or
  update the matching entry in
  [design/open-questions.md](design/open-questions.md).
- **Planning a cross-block implementation flow** → add or update its
  implementation-flow sketch in the relevant design document, and the
  milestone's `tickets/<milestone>/implementation-flow.md` (one section per
  ticket, in order, with that ticket's mock shapes), before relying on it in
  tickets.
- **Quoting history** → link the raw file; never treat it as the current
  specification.

## Verified current state

Checked against the working tree on 2026-11-16:

- `scrapers/sites.py` (974 lines) is the active combined implementation:
  `BaseScraper`, `KarriereAT`, `Raiffeisen`. `scrapers/__init__.py` exports from
  it. `scrapers/basescraper.py` (417 lines) contains a near-duplicate copy of
  `BaseScraper` (0.995 text similarity at review);
  `scrapers/websites/karriere_at.py` and `raiffeisen.py` contain close variants
  of the site classes. The split modules are not the public path.
- `schedule/hardverapro_collect.py` imports
  `jobscraping.scrapers.websites.hardverapro`, a module that is absent from the
  tree (only a stale `__pycache__` entry remains). `schedule/` is mostly
  Git-ignored.
- `pipelines/collecting.py` mixes the legacy profile flow (`get_postings`) with
  reusable acquisition helpers (`scrape_sites`, `validate_postings_quality`)
  that `pipelines/scrape_universal.py` imports.
- `pipelines/scrape_universal.py::run_universal_scrape_flow` is the current
  universal-collector equivalent: it owns scope, cache, acquisition, quality and
  storage in one function. There is no separately named collector.
- `processing/postings_utils.py` imports `scrapers.sites.BaseScraper` inside
  `enrich_postings`, so processing depends on scraping.
- `processing/derive_profile_postings.py` defaults to Dani constants and calls
  Dani policy functions, so derivation is not yet profile-neutral.
- `processing/candidate_filtering.py`, `selection_filtering.py` and `scoring.py`
  are empty placeholders. `profiles/dani.py` holds the working policy.
- `processing/language_requirements.py` contains the only existing frozen
  dataclass (`LanguageEvidence`); it is the precedent for the specs-and-dataclasses
  discussion.
- `config/configs.py` hardcodes an absolute Windows repository root
  (`REPO_ROOT_PATH`), so paths work only on one machine. Removing it is part of
  the migration.
- More job sites are planned soon. Today a new site would start as another copy
  of `BaseScraper` and its site class.
- `pyproject.toml` targets Python `>=3.13.17`. Kedro 1.8.0 and kedro-datasets
  10.0.0 accept 3.13 (PyPI classifiers, checked 2026-11-16), so the requested
  Kedro adoption is feasible on the current interpreter.

## Decision log

Confirmed decisions are binding. Only Q16 remains open; the full decision log is
[design/open-questions.md](design/open-questions.md).

| # | Decision | State |
| --- | --- | --- |
| D1 | Collection is profile-neutral; profiles own relevance, scoring and selection. | Confirmed — [ADR 0001](../../docs/adr/0001-collection-and-profile-ownership.md) |
| D2 | Two profile filters: a broad candidate filter and a final selection filter. | Confirmed as a working model; may merge later |
| D3 | Dani is the first profile migrated to the separated path. | Confirmed |
| D4 | Refactor by moving behaviour first, improving only after parity. | Working principle |
| D5 | Each pipeline step declares a data spec (the fields it needs and produces); dataclasses are limited to specs and YAML-backed config. | Confirmed 2026-11-16 — [design/specs.md](design/specs.md) |
| D6 | Kedro becomes the pipeline runtime. | Requested; implementation owned by the user — [design/kedro-project.md](design/kedro-project.md) |
| D7 | `conf/` owns run-tunable configuration; `config/` keeps code constants. | Confirmed 2026-11-16 |
| D8 | The topic keeps this document ladder plus a raw archive. | Confirmed 2026-11-16 |
| D9 | The raw archive stays local-only and Git-ignored. | Confirmed 2026-11-16 |
| D10 | Site adapters declare their own ordered steps; steps can be skipped and failures produce partial results plus an alert. No required-step flags or enforcement machinery. | Confirmed 2026-11-16 — [design/collection-steps.md](design/collection-steps.md) |
| D11 | A universal collector orchestrates adapters across query units and owns the vault. | Requested direction |
| D12 | Collection and profile tunables live in `conf/` YAML and are loaded into config objects. | Confirmed direction |
| D13 | Drop separate `ArtifactPaths`, `QualityPolicy`/`QualityReport` and `ScoringConfig` dataclasses; fold scoring and language values into profile config. | Confirmed 2026-11-16; quality report deferred |
| D14 | Posting records remain dicts on export; dataclasses may model related data, and the existing schema is not enforced. | Confirmed 2026-11-16 |
| D15 | Add `specs/`, `acquisition/` and `data/` as new modules; do not keep everything under `pipelines/` and `processing/`. | Confirmed 2026-11-16 |
| D16 | No absolute paths. Derive the repository root from `__file__` and keep configured paths relative. | Confirmed 2026-11-16 |
| D17 | Split HTTP and headless-browser scraping behind a facade; pagination stays shared. | Confirmed 2026-11-16 |
| D18 | Universal collection stores every posting; profiles do the filtering. A profile `current_postings.json` holds selected postings only. | Confirmed 2026-11-16 |
| D19 | `conf/` holds anything a user tunes; site selectors stay in the adapter file; specs stay in code. | Confirmed 2026-11-16 |
| D20 | Kedro starts with collection plus storing and other nodes, not a universal pipeline; more nodes are expected and may replace `_collect` scripts. | Confirmed 2026-11-16 |
| D21 | No `ProfilePolicy` wrapper and no scoring class; delete the three empty processing modules. | Confirmed 2026-11-16 |
| D22 | No per-spec digest or old-data compatibility requirement; a vault `schema_version` is enough. | Confirmed 2026-11-16 |
| D23 | The universal history is expected but not guaranteed. Collection may be planned per pipeline; profiles and stages take their input records as arguments and never assume one universal history exists. | Confirmed 2026-11-22 — Q28 |
| D24 | Universal records carry profile-neutral annotations (`language`, `guessed_required_languages`, `matched_titlewords`); policy fields stay in scored/selected, and enrichment in `data/enrich.py` produces the language facts. | Confirmed 2026-11-24 — Q29 |
| D25 | A site is a class in its own module and is its own adapter. `BaseScraper` shrinks to per-run setup (rules/keywords/date), `source` and the declared `steps` — no overridable helper methods; shared mechanics are module functions and per-site differences are arguments or `rules` keys. | Confirmed 2026-11-24 — Q30 |

## The three mandated directions

These are required regardless of the final design:

1. **True separations.** Parts that can be separated become separate
   files/modules with one responsibility: `specs/`, `acquisition/` and `data/`
   are added, HTTP and browser mechanics split, and each site is one adapter
   module. The map is [design/module-seams.md](design/module-seams.md), the
   collection model is [design/collection-steps.md](design/collection-steps.md),
   and the workstreams are [breakdown/collection.md](breakdown/collection.md)
   and [breakdown/pipelines.md](breakdown/pipelines.md).
2. **Specs and minimal dataclasses.** Each step declares a data spec: the key and
   the fields it needs and produces. That is the "start from here" contract;
   dataclasses are limited to data specs and YAML-backed config, and posting
   records stay dicts. Candidates and dropped ideas are in
   [design/specs.md](design/specs.md).
3. **Kedro for pipelines.** Adopt Kedro with `conf/`, parameters, catalog
   entries and node/flow composition. The user builds the graph, starting with
   collection plus storing. Layout and migration guidance are in
   [design/kedro-project.md](design/kedro-project.md); the workstream is
   [breakdown/pipelines.md](breakdown/pipelines.md).

## Related material outside this topic

- [Language correction plan](../language_correction_plan.md) and
  [implementation notes](../language_correction_implementation.md): feature
  work that also constrains the Dani migration.
- [Glossary](../../GLOSSARY.md): vocabulary the documents rely on.
- Raw scratch material that mixes refactoring with unrelated ideas:
  [TODO](../raw/TODO.md), [CRITIQUE](../raw/CRITIQUE.md),
  [new ideas](../raw/new_ideas.txt). Not copied here.
