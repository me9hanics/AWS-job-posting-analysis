# Module seams

Status: decided 2026-11-16 for grouping and mechanics split. This document
names the parts that can be separated today, the parts that should stay
together, and the import directions that keep the separation real. It is the
"true separations" direction in concrete form.

Three new modules are added: `specs/`, `acquisition/` and `data/` (Q1). The
mechanics file splits into HTTP and headless-browser paths (Q2). More sites are
coming, so a site must be addable without touching the collector (A14).

## Dependency rules

```mermaid
flowchart TD
    config[config]
    specs[specs]
    utils[utils]
    io[io]
    scrapers[scrapers]
    acquisition[acquisition]
    data[data]
    processing[processing]
    profiles[profiles]
    pipelines[pipelines]

    utils --> config
    io --> config
    io --> utils
    scrapers --> io
    scrapers --> specs
    acquisition --> scrapers
    acquisition --> data
    acquisition --> specs
    data --> io
    data --> specs
    processing --> data
    processing --> specs
    profiles --> processing
    profiles --> specs
    pipelines --> profiles
    pipelines --> acquisition
```

Allowed direction is upward only:

| Module | May import | Must not import |
| --- | --- | --- |
| `specs` | stdlib | anything in the package |
| `config` | stdlib | everything else |
| `utils` | `config` | everything else |
| `io` | `config`, `utils` | `specs`, `processing`, `profiles`, `scrapers`, `pipelines` |
| `scrapers` | `config`, `utils`, `io`, `specs` | `processing`, `profiles`, `pipelines` |
| `acquisition` | `config`, `io`, `scrapers`, `data`, `specs` | `profiles`, `pipelines` |
| `data` | `config`, `io`, `utils`, `specs` | `scrapers`, `acquisition`, `profiles`, `pipelines` |
| `processing` | `config`, `data`, `io`, `utils`, `specs` | `scrapers`, `acquisition`, `profiles`, `pipelines` |
| `profiles` | `config`, `processing`, `data`, `utils`, `specs` | `scrapers`, `acquisition`, `pipelines` |
| `pipelines` | everything | — |

`specs` is a leaf because a site adapter, a data operation and a profile
derivation must all agree on field names without importing each other.

Detection is a fact, not a policy: `data` owns the text-language and salary
detectors because `data/enrich.py` produces the profile-neutral annotations
(D24, Q29) and must not import `processing`. There is exactly one
`language.py`, under `data/`: detection and requirement evidence. Language
*policy* (`assess_language`, adjustments, exclusions) stays with the profile
that owns it, and `processing` keeps only scoring and derivation helpers.

`scrapers/http.py` and `scrapers/browser.py` have different dependencies and
failure modes. One `scrape.py` facade keeps call sites stable during the move;
the facade is removed when no caller needs it. Pagination is shared because both
paths construct the same query URLs.

Adding a site: one module under `scrapers/websites/` plus one entry in the
registry used by the collector. The adapter owns parsing, selectors and its step
list. No collector, data or profile edit. There is still no plugin framework;
the registry is an explicit list.

Paths: no absolute paths. `REPO_ROOT` is derived from `__file__` in one place
(see [open-questions.md](open-questions.md#no-absolute-paths)); every catalog or
config path is relative to it. Tests use relative paths or `tmp_path`.

### Current violations (verified 2026-11-16)

| Violation | Where | Why it matters |
| --- | --- | --- |
| `processing` → `pipelines` | `derive_profile_postings.py` imports `load_postings`, `merge_observations` from `pipelines.store_universal` | A lower layer depends on the composition layer; the data functions cannot be reused or tested alone. |
| `processing` → `profiles` | `derive_profile_postings.py` imports Dani constants and policy functions | Generic derivation is profile-specific; a second profile forces an edit here. |
| `processing` → `scrapers` | `postings_utils.py` imports `BaseScraper` inside `enrich_postings` | Re-enrichment pulls in Selenium, requests and scraper configuration. |
| Duplicate implementations | `scrapers/sites.py` vs `scrapers/basescraper.py` and `scrapers/websites/*` | Two copies of the same classes; callers and fixes can drift. Every new site would otherwise start as another copy. |
| Absolute path | `config/configs.py` hardcodes an absolute Windows repository root (`REPO_ROOT_PATH`) | The package only works on one machine and leaks a local path into config. Replace with a root derived from `__file__`. |
| Empty modules | `processing/candidate_filtering.py`, `selection_filtering.py`, `scoring.py` | Names promise behaviour that does not exist; delete them and let profile functions plus `processing/scoring_mechanics.py` own the roles (Q15). |
| Stale module | `schedule/hardverapro_collect.py` imports a missing module | Archive-only one-off; not a migration gate (Q17). |

## Target package map

Proposed names. Renames are cheap; ownership is the point.

```text
src/jobscraping/
  specs/
    base.py               # FieldSpec, DataSpec, check
    postings.py           # DataSpec constants: discovered, collected, universal, scored
    companies.py          # only when a real side export exists
  config/
    constants.py          # filenames, column layout, request constants
    models.py             # CollectionConfig, ProfileConfig (YAML-backed)
    configs.py            # split later; keep during migration
  utils/
    urls.py
    datastruct_utils.py
  io/
    files_io.py           # JSON load/save, listing, filename selection
    outputs_excel.py      # Excel rendering and cleaning
    outputs.py            # Markdown/email + current compatibility caller
    generate_profile_outputs.py
  scrapers/
    scrape.py             # facade during the split
    http.py               # requests path
    browser.py            # Selenium session, popups, scrolling
    pagination.py         # URL construction and next-page rules
    parsing.py            # payload -> neutral facts
    steps.py              # optional Step convenience, no enforcement
    basescraper.py        # run context, source, steps; one copy, no hooks
    websites/
      __init__.py         # public exports + registry
      karriere_at.py      # adapter + its declared steps
      raiffeisen.py
      <next_site>.py      # one module per new site
  acquisition/
    collector.py          # run_collection: adapters, units, steps, merge
    quality.py            # validate_postings_quality and gates
    chunks.py             # chunk naming, save, load, resume
  data/
    load.py               # persistence wrapper, relative paths, atomic write
    merge.py              # merge_observations, history rebuild
    compare.py            # neutral added/removed diff
    enrich.py             # rerunnable generic enrichment
    language.py           # text language + requirement evidence (moved from processing)
    salary.py             # salary detection without a scraper
  processing/
    facts.py              # factual_postings and normalization
    scoring_mechanics.py  # scoring mechanics, profile-agnostic
    derive.py             # generic profile derivation
  profiles/
    dani.py               # policy functions and config defaults
  pipelines/
    collection.py
    derivation.py
    outputs.py
    cli.py
```

## Current → target mapping

| Current | Target | Reason |
| --- | --- | --- |
| `scrapers/sites.py` (`BaseScraper` + sites, 974 lines) | `scrapers/basescraper.py`, `scrapers/websites/*` | Active copy plus duplicated copies elsewhere; one owner per class. |
| `scrapers/scrape.py` (659 lines) | `http.py`, `browser.py`, `pagination.py` behind a `scrape.py` facade | HTTP and browser have different dependencies and failure modes. |
| `BaseScraper.gather_data` + `process` flag | adapter steps + `scrapers/steps.py` + collector selection | Sites differ in how many requests and which data they can supply; one flag cannot express that. |
| `BaseScraper._process_data` chain | `processing/` + `profiles/` | Profile processing is not scraper mechanics. |
| `processing/postings_utils.py` (514 lines) | `data/merge.py`, `data/compare.py`, `data/enrich.py`, `processing/facts.py` | Historical mix of pure data, enrichment and a scraper import. |
| `pipelines/store_universal.py` | `data/load.py`, `data/merge.py`, `acquisition/collector.py` + thin pipeline | Storage and merge are pure; scope and orchestration belong to the collector. |
| `pipelines/scrape_universal.py::run_universal_scrape_flow` | `acquisition/collector.py` + pipeline | One function owns scope, cache, acquisition, quality and storage. |
| `pipelines/collecting.py` helpers | `acquisition/collector.py`, `acquisition/quality.py` | Reusable acquisition sits inside the legacy pipeline. |
| `processing/derive_profile_postings.py` | `processing/derive.py` + profile policy functions | Generic derivation with a policy input; no wrapper class. |
| `processing/attributes.py` | `data/language.py`, `data/salary.py`, `processing/scoring_mechanics.py`, `data/enrich.py` | Detection (a fact, used by enrichment), scoring (policy mechanics) and enrichment are different reasons to change. |
| `config/configs.py` | `config/models.py`, `config/constants.py`, `specs/`, `conf/` | Config values, code constants and data-spec field names are three different things. |

## Canonical copies (B11)

Three copy sets exist; `sites.py` is canonical for all three classes.

| Class | Canonical | Also present (stale) | Evidence |
| --- | --- | --- | --- |
| `BaseScraper` | `scrapers/sites.py` | `scrapers/basescraper.py` | Owns `date_day`, the `process=False` raw path, cache split and `factual_postings`; the copy lacks them and builds `business_day` differently. |
| `KarriereAT` | `scrapers/sites.py` | `scrapers/websites/karriere_at.py` | Same `__init__`/`gather_data` as the base it must match; the copy predates `process`. |
| `Raiffeisen` | `scrapers/sites.py` | `scrapers/websites/raiffeisen.py` | Holds `collected_on` in the listing and fetches per-posting details when `process=False`. |

`scrapers/__init__.py` imports from `sites.py`, so the B05 fixture parity tests
(`tests/test_scraper_fixtures.py`, 6 tests) already exercise the canonical copy;
they pass as recorded in the milestone flow. The stale copies are **overwritten**
by the moves in B12–B14, never merged: there is no third copy to reconcile later.

## Site class and its base

A site is **one class in its own module**, and that class is the adapter. The
class is not a thin shell over inherited machinery, and `BaseScraper` is not a
hook surface (Q30):

```python
class Raiffeisen(BaseScraper):
    source = "raiffeisen_international"          # the adapter contract (B09)

    def __init__(self, **kwargs):
        super().__init__(rules=RAIFFEISEN_RULES, **kwargs)
        self.steps = (Step("listings", self.listings),
                      Step("details", self.details, output_spec=COLLECTED_POSTINGS))
```

`BaseScraper` keeps the parts every run needs and no site would sensibly
replace: config normalization (`rules`, `keywords`, `rankings`, `locations`,
`transformations`), per-run state (`time`, `day`, `business_day`, `date_day`),
`source` and `steps`. It declares **no** `gather_data` template and no
helper methods for sites to override.

Everything else is a module function the site calls: `pagination` (URLs, next
page), `browser` (session, popups, scrolling), `http` (requests), `parsing`
(payload → facts). Per-site differences are arguments or `rules` keys — a
conversion rate, a selector, a regex — not overridden methods. The base's module
docstring names the mechanics modules once; it does not mirror their API.

A step is declared by the site class, typically as a bound method, so per-run
state (cookies, tokens) is available without a base hook:

```python
def listings(self, records: RecordSet, config: CollectionConfigLike) -> RecordSet: ...
```

Why: the two existing sites both override `gather_data` wholesale and Raiffeisen
overrides `_process_posting_soups` with a different signature, so the old hook
contract was already vestigial; it made "add a site" mean "copy the base class".
Inheritance still carries the run context; it no longer carries an algorithm to
override.

Rejected alternative: an empty `gather_data` raising `NotImplementedError` as a
"you must implement this" prompt — it re-declares the algorithm shape the base
just dropped and competes with `steps` as the contract, so the base declares
`source` and `steps` and nothing else to implement.

## Seams deliberately not made

- **Posting records stay dicts.** JSON export implies dicts; a `Posting`
  dataclass would force a full schema on heterogeneous optional fields. Data
  specs validate the fields we rely on, and unknown keys are preserved.
- **No per-dataclass decomposition.** `ArtifactPaths`, `QualityPolicy`,
  `ScoringConfig` and similar wrappers are dropped; see
  [specs.md](specs.md).
- **No storage repository abstraction.** `files_io` is enough until a second
  backend has a consumer.
- **Excel rendering and its cleaning helpers stay together.** They change for
  the same reason.
- **`BaseScraper` stays a class, but not a hook surface.** It carries run
  context and the adapter contract (`source`, `steps`); helper methods are not
  overridden — they are module functions, and per-site differences are arguments
  or `rules` keys (Q30, [above](#site-class-and-its-base)).
- **No plugin/discovery system for sites.** Adding a site is one module and one
  registry entry; the registry is an explicit list, not a framework.
- **No `ProfilePolicy` wrapper.** Profile functions and `ProfileConfig` are
  passed to the generic derivation directly (Q5).
- **No scoring class.** Scoring stays values plus the shared mechanics (Q4).
- **No absolute paths.** Paths come from a runtime-derived repository root; no
  module stores a machine-specific root.

## Seam test

Before creating a module, answer:

1. Can it be imported without a browser, a network call or a profile module?
2. Does it have one reason to change, and can that reason be named?
3. Can it run from saved artifacts or a small fixture alone?
4. Does its test avoid another part's fixtures?
5. Is there exactly one kind of caller (or one pipeline) that needs it?

A "no" is a reason to keep the code where it is until the seam is real.

## Migration notes

- Add `specs/` and the step contract before moving site bodies: the contract is
  what the moved code must satisfy.
- Collapse the duplicate scrapers before adding more sites. Otherwise every new
  site multiplies the duplication.
- Move the classes first, then split the mechanics file; splitting both at once
  makes parity unverifiable. HTTP and browser split is the target, not a
  prerequisite for moving site bodies.
- Keep `scrape.py` as a facade re-exporting moved helpers so call sites do not
  change during the move.
- Keep `config/configs.py` in place during migration; derive the root from
  `__file__` there first, so every path becomes relative before anything moves.
- Delete the three empty processing modules when derivation owns the roles; do
  not rename them into permanent placeholders.
- The target tree is not a license to rename everything: renames must pay for
  themselves in clarity or remove a duplicate.
