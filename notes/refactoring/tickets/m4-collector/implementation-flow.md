# M4 implementation flow — collector

Status: plan, 2026-11-25. The milestone's own view of what B19–B25 build and
where each piece sits. Tickets run in order; each gets its own chain and the mock
shapes it introduces. Mock code shows boundaries only — it is never imported or
copied verbatim.

`In → Does → Out → Next`, per ticket. A ticket whose parts are not continuous
gets one chain per part; a ticket that builds one continuous segment gets one
chain.

Design sources: [collection-steps.md](../../design/collection-steps.md) for the
adapter/step contract and collector rules, [artifacts.md](../../design/artifacts.md)
for chunks, the run report and the vault, [specs.md](../../design/specs.md) for
`CollectionConfig` and the posting specs, [module-seams.md](../../design/module-seams.md)
for module ownership and Q30. M3 ended with one `BaseScraper`, HTTP / browser /
pagination split, no `scrape.py`, and the step contract proven by
`tests/test_steps_contract.py`.

## Decisions this plan fixes

1. **`CollectionConfig` becomes concrete in B22**, in
   `src/jobscraping/config/models.py`, with the [specs.md](../../design/specs.md#collectionconfig)
   shape. B32 later adds `ProfileConfig` to the same module; it does not create
   the file.
2. **Cache is a config input, not a scope field.** `cached_postings` and
   `cache_hit_predicate` join `cache_mode` on `CollectionConfig` and are
   excluded from `scope_digest()`. A `details` step reads them; no marker field
   enters the record. The design edit is already in
   [specs.md](../../design/specs.md#collectionconfig) and
   [collection-steps.md](../../design/collection-steps.md).
3. **A unit is `(source, step)` in M4.** Each adapter's `listings` step owns its
   query × location loops, because `Step.run` receives `(records, config)`, not
   a unit. Chunks are therefore
   `chunks/<scope-digest>/<source>/<step>.json`. Per-query chunks wait for a
   step-level unit argument.
4. **The collector records; the pipeline decides.** `run_collection` never
   aborts a run on a step error and never touches the vault. It returns
   `{"records", "report"}` and, when given an artifact path, writes only chunks
   and the run report. The pipeline runs the quality gate, stores the vault and
   raises on a failed report (B24).
5. **The cache split belongs to `details`.** That is the step it saves work in.
   A listings-only run is a discovery run and does not merge cached facts; this
   narrows today's `gather_data(descriptions=False)` only for the unused
   "listings plus cache, no details" combination.
6. **Wrappers live while named callers live (Q16 default).**
   `KarriereAT.gather_data` / `Raiffeisen.gather_data` become wrappers in
   B19/B20 and keep serving the legacy `get_postings` path until B44;
   `scrape_sites` stays for that path after B24. B24 stops the universal path
   from calling either.

---

## B19 — `KarriereAT` declared steps

B21 is independent of B19/B20 and may land first; it touches neither site
module.

- **In:** `config` (cache fields) and the shared record set (empty for a fresh
  unit), plus the adapter's existing run context (`rules`, `keywords`,
  `business_day`, `csrf_token`).
- **Does:** the raw half of today's `gather_data` becomes two bound-method
  steps: `listings` builds identity records from search pages; `details` splits
  the cache and fetches descriptions for the misses. Both reproduce the
  `process=False` branches exactly (`terminal_http_statuses=(410,)`,
  `raise_on_http_error=True`, `raise_on_retry_failure=False`).
- **Out:** a `RecordSet` that satisfies `DISCOVERED_POSTINGS` after `listings`
  and `COLLECTED_POSTINGS` after `details` (`description` may be absent).
- **Next:** B20 copies the shape; B22 runs the steps; B24 stops calling
  `gather_data`.

```python
# src/jobscraping/scrapers/websites/karriere_at.py
class KarriereAT(BaseScraper):
    source = "karriere.at"

    def __init__(self, ..., date_day=None):
        ...                                   # rules/keywords normalization as today
        self.steps = (
            Step("listings", self.listings, output_spec=DISCOVERED_POSTINGS),
            Step("details", self.details, input_spec=DISCOVERED_POSTINGS,
                 output_spec=COLLECTED_POSTINGS),
        )

    def listings(self, records: RecordSet, config) -> RecordSet: ...
    def details(self, records: RecordSet, config) -> RecordSet: ...
```

`details` keeps today's cache semantics by calling the existing helper with the
config values, then returning hits and misses together:

```python
hits, misses = split_cached_postings(
    records,
    cached_postings=config.cached_postings,
    cache_mode=config.cache_mode,
    cache_hit_predicate=config.cache_hit_predicate,
)
...                                           # one cookie request for the misses' ids
return {**hits, **misses}                     # misses keep missing descriptions
```

`gather_data` keeps its signature and its `process=True` body, and delegates the
`process=False` branch to the steps plus `factual_postings`. It stays until the
legacy `get_postings` path is removed (B44); B24 only stops the universal path
from reaching it. The `_salary_from_text` override is deleted — `listings` calls
`processing.attributes.salary_from_text` with the site keywords and
`conversion_rate=14`. No helper method is added to or overridden on
`BaseScraper`; `gather_data` is the single retained compatibility override.

## B20 — `Raiffeisen` declared steps

- **In:** the same config slice, plus Raiffeisen's rules (`usecase`,
  `request_wait_time`, `gather_data_selector`, `more_pages_url_extension`,
  `jobs_base_url`).
- **Does:** `listings` paginates per titleword and parses listing soups;
  `details` splits the cache and fetches one detail page per miss, so a failed
  detail cannot shift another ID's soup. Site-specific parsing stops being
  methods on the class: it moves to module functions in the same file.
- **Out:** the same records as the raw half of today's `gather_data`.
- **Next:** B22 runs both adapters; B25 proves the collector needs no edit per
  site.

```python
# src/jobscraping/scrapers/websites/raiffeisen.py
def page_urls(titlewords: tuple[str, ...], base_url: str) -> list[str]: ...
def parse_listing_soups(soups, titles_pattern, website, jobs_base_url) -> RecordSet: ...
def parse_detail_soups(id_soup_dicts, verbose=False) -> dict: ...
def clean_variables(variables) -> list: ...

class Raiffeisen(BaseScraper):
    source = "raiffeisen_international"

    def __init__(self, ..., date_day=None):
        ...
        self.steps = (
            Step("listings", self.listings, output_spec=DISCOVERED_POSTINGS),
            Step("details", self.details, input_spec=DISCOVERED_POSTINGS,
                 output_spec=COLLECTED_POSTINGS),
        )

    def listings(self, records: RecordSet, config) -> RecordSet: ...
    def details(self, records: RecordSet, config) -> RecordSet: ...
```

The base-name overrides go: `_construct_page_urls`, `_process_posting_soups`,
`_next_page_logic` and `_salary_from_text` become module-function calls
(`page_urls`, `parse_listing_soups`, `pagination.next_page_logic_by_length`,
`attributes.salary_from_text`). `gather_data(process=True)` keeps today's
batched detail fetch and `_process_data`; `process=False` delegates to the
steps. `tests/test_scraper_fixtures.py::RaiffeisenHelperParsingTests` is
retargeted to the module functions; fixture facts do not change.

## B21 — the quality gate moves

- **In:** `collecting.validate_postings_quality` and its callers
  (`get_postings`, `run_universal_scrape_flow`).
- **Does:** move the function unchanged into the new `acquisition` package;
  `collecting` re-exports the name so existing imports and patches keep working.
- **Out:** `src/jobscraping/acquisition/quality.py` with no profile import; a
  thinner `collecting.py`.
- **Next:** B24 calls it around `run_collection`; B36 may move the call into the
  collection stage.

```python
# src/jobscraping/acquisition/quality.py
def validate_postings_quality(postings, previous_postings=None,
                              required_fields_by_source=None,
                              minimum_source_retention=None,
                              minimum_field_completeness_by_source=None,
                              verbose=False) -> None: ...

# src/jobscraping/pipelines/collecting.py
from jobscraping.acquisition.quality import (        # noqa: F401  (re-export)
    validate_postings_quality,
)
```

Tests: `tests/test_quality_gate.py` (pass and fail per-source field and
retention thresholds). The collector does **not** call the gate in M4
(B22 returns data only).

## B22 — the universal collector

- **In:** constructed adapter instances (`source`, ordered `steps`) and one
  `CollectionConfig`; B23 adds an optional artifact path, so this ticket stays
  file-free.
- **Does:** per adapter, run each declared step in order, honour
  `config.steps` (empty = all), catch a step error, keep later steps running,
  flag an empty result, and merge site results by identity.
- **Out:** `{"records": RecordSet, "report": ...}` with per-step outcomes.
- **Next:** B23 writes chunks and the report; B24 stores and gates; B37 adds
  spec checks; B38 adds chunk reuse.

```python
# src/jobscraping/config/models.py   (new; ProfileConfig joins in B32)
@dataclass(frozen=True)
class CollectionConfig:
    sites: tuple[str, ...] = ()
    queries: tuple[str, ...] = ()
    locations: tuple[str, ...] = ()
    steps: tuple[str, ...] = ()
    overrides: Mapping[str, object] = field(default_factory=dict)
    cache_mode: str | None = None
    cached_postings: Mapping[str, dict] = field(default_factory=dict)
    cache_hit_predicate: Callable | None = None
    def scope_digest(self) -> str: ...          # scope fields + overrides only

# src/jobscraping/acquisition/collector.py
def run_collection(adapters, config) -> dict:
    # {"records": RecordSet,
    #  "report": {
    #      "scope_digest": str,
    #      "sites": [{"source": str, "failed": bool,
    #                 "steps": [{"name": str,
    #                            "status": "ok" | "skipped" | "failed" | "empty",
    #                            "records": int | None,
    #                            "error": str | None}]}],
    #      "failed": bool, "zero_records": bool}}
```

`scrapers/steps.py::CollectionConfigLike` already carries the two cache fields
from B19; B22 supplies the concrete values and corrects the protocol docstring
that still said the concrete config lands with B32. The collector imports
`Step` (for the plain-pair form) but no site module and no profile.

## B23 — chunks and the run report

- **In:** the collection result from B22, the config digest, and the artifact
  path the pipeline supplies.
- **Does:** write one chunk after each `ok` step; write the report once. Skipped,
  failed and empty steps write no chunk. A rerun of the same digest, source and
  step replaces its file.
- **Out:** `chunks/<digest>/<source>/<step>.json` and `run_report.json` under the
  vault path.
- **Next:** B24 passes the path; B38 reuses valid chunks and reads the report.

```python
# src/jobscraping/acquisition/chunks.py
def chunk_path(path, scope_digest, source, step) -> Path: ...
def write_chunk(path, scope_digest, source, step, records) -> Path:
    # file content: {"source": source, "step": step, "records": records}
def write_report(path, report) -> Path: ...        # <path>/run_report.json

# src/jobscraping/acquisition/collector.py
def run_collection(adapters, config, artifact_path=None) -> dict: ...
```

`files_io.save_data(..., with_timestamp=False)` is the writer until B30 replaces
it with an atomic write. `artifact_path=None` keeps B22's return-only behaviour
for unit tests. Tests start in `tests/test_collector.py` (B22 creates the
module, B25 extends it).

## B24 — the universal pipeline uses the collector

- **In:** today's `run_universal_scrape_flow` arguments (`path`, `scrapers`,
  `keywords`, `cache_mode`, `cache_hit_predicate`, `seed_history`, quality
  arguments, `**kwargs`) and the cache/seed it already loads.
- **Does:** build adapters with the same constructor mapping `scrape_sites`
  uses (extracted to a shared `build_scraper`), build the `CollectionConfig`
  (cache in the config, no cache data in the scope), call `run_collection(...,
  artifact_path=path)`, raise when the report says failed, then run the quality
  gate and `store_universal_postings` as today.
- **Out:** the same vault files as before, plus chunks and `run_report.json`.
- **Next:** B25 pins the behaviour; B31 changes what is stored.

```python
# src/jobscraping/pipelines/collecting.py
def build_scraper(scraper_class, *, keywords, rankings, salary_bearable,
                  date_day=None, **kwargs): ...        # extracted verbatim
# scrape_sites() calls build_scraper(); behaviour unchanged

# src/jobscraping/pipelines/scrape_universal.py
adapters = [build_scraper(cls, keywords=keywords, rankings=rankings,
                          salary_bearable=salary_bearable, date_day=date_day,
                          **kwargs) for cls in scrapers]
config = CollectionConfig(
    sites=tuple(adapter.source for adapter in adapters),
    queries=tuple(sorted(set(keywords.get("titlewords", [])))),
    locations=tuple(keywords.get("locations", [])),
    steps=(),
    overrides=overrides,
    cache_mode=cache_mode,
    cached_postings=factual_postings(cache),
    cache_hit_predicate=cache_hit_predicate,
)
result = run_collection(adapters, config, artifact_path=path)
raw = factual_postings(result["records"])
if result["report"]["failed"]:
    raise RuntimeError(failure_message(result["report"]))
...                                  # quality gate, incomplete run, store as today
```

`overrides` is the same dict the pipeline already builds for `collection_scope`,
and `collection_scope.json` keeps its current content so `same_scope` and the
retention baseline do not change on the switch. `failure_message` embeds each
failed step's recorded error verbatim, so the existing "HTTP 410" expectation
still matches. The legacy `get_postings` / `scrape_sites` path is untouched.

The WIP module `tests/test_raw_collection.py` builds fake sources with only
`gather_data`; its `run_universal_scrape_flow` cases are updated to one-step
adapters in this ticket. No compatibility branch for step-less adapters is added
to the pipeline.

## B25 — collector integration tests

- **In:** `run_collection`, fake adapters, a temporary artifact path.
- **Does:** assert the five required behaviours end to end: one-shot and
  two-step adapters; a skipped detail step with partial records and no chunk; a
  raising step that names its error and does not stop later steps; zero records
  as a failure; and a new fake site that needs only a module plus one registry
  entry.
- **Out:** `tests/test_collector.py` covering the collector contract.
- **Next:** M5 stores what this returns; B38 adds resume tests on the same
  module.

```python
class FakeNewSite:
    source = "fake.test"
    steps = (Step("all", fetch_everything, output_spec=COLLECTED_POSTINGS),)

ADAPTERS = [FakeNewSite]              # the one registry entry; no collector edit
```

---

## The milestone end to end

After B19–B25 the universal path is one call boundary, and the legacy profile
path still runs through the old call shape:

```text
run_universal_scrape_flow(path, scrapers, keywords, cache…, seed_history)  (B24)
  -> build_scraper per class, same kwargs mapping as scrape_sites           (B24)
  -> CollectionConfig(sites, queries, locations, steps, overrides,
                      cache_mode, cached_postings, predicate)              (B22)
  -> run_collection(adapters, config, artifact_path=path)
       per adapter: listings -> details, selection, error capture,
                    merge by identity                                  (B19/B20/B22)
       chunks/<digest>/<source>/<step>.json + run_report.json          (B23)
  -> report failed? raise, vault untouched                                 (B24)
  -> factual_postings -> validate_postings_quality -> store_universal      (B21/B24)
  -> vault: current / history / newly added / scope                        (unchanged)

legacy: schedule/*_collect -> get_postings -> scrape_sites
        -> KarriereAT.gather_data / Raiffeisen.gather_data (wrappers, until B44)
```

## Gates for the milestone

- `uv run python -m unittest discover -s tests` → `OK`. Report the count the
  runner prints, not a pinned number; the 30 WIP tests from
  `test_dani_profile.py`, `test_language_requirements.py` and
  `test_raw_collection.py` stay green.
- `rg "class BaseScraper|class KarriereAT|class Raiffeisen" src` → three matches.
- `rg "from jobscraping.scrapers.websites|KarriereAT|Raiffeisen" src/jobscraping/acquisition` → none.
- `rg "profiles|profile" src/jobscraping/acquisition` → none (quality and
  collector stay profile-free).
- `rg "def _salary_from_text|def _process_posting_soups|def _construct_page_urls|def _next_page_logic|def next_page_logic" src/jobscraping/scrapers/websites` → none after B20.
- `gather_data` in `src/jobscraping/pipelines/scrape_universal.py` → none after
  B24.
- New code in B19–B25 passes `uvx ruff check` and `uvx ty check`. Findings in
  code these tickets only move — the legacy `gather_data` bodies, base helpers,
  old profile pipelines — are reported, not fixed. A "too many arguments"
  finding is raised with the user instead of being worked around.
- A failed run leaves `current_postings.json` and `postings_history.json`
  byte-identical and writes one run report and one incomplete-run artifact.
- Ticket status rows in [tickets/README.md](../README.md) updated in the same
  change as each ticket. Work stays in the working tree: no commits for B19–B25.

## Document updates made with this plan

- [specs.md](../../design/specs.md#collectionconfig): cache inputs on
  `CollectionConfig`, excluded from the digest.
- [artifacts.md](../../design/artifacts.md#resume-and-failure): M4 chunk unit and
  path, and the report filename.
- [collection-steps.md](../../design/collection-steps.md#universal-collector):
  what the collector does in M4 versus what the pipeline keeps; cache inputs in
  the config.

Q16 stays as written: wrappers exist only while named callers exist. B19/B20
name `gather_data` as the wrapper, B24 names the legacy `scrape_sites` path, and
B44 removes both.
