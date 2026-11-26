# M5 implementation flow — data layer

Status: plan, 2026-11-26. The milestone's own view of what B26–B31 build and
where each piece sits. Tickets run in order; each gets its own chain and the mock
shapes it introduces. Mock code shows boundaries only — it is never imported or
copied verbatim.

`In → Does → Out → Next`, per ticket. A ticket whose parts are not continuous
gets one chain per part; a ticket that builds one continuous segment gets one
chain.

Design sources: [module-seams.md](../../design/module-seams.md) for module
ownership and the dependency arrows, [artifacts.md](../../design/artifacts.md)
for vault files, merge rules and write safety, [specs.md](../../design/specs.md)
for `UNIVERSAL_POSTINGS` and the profile-neutral annotations. M4 ended with the
universal path calling `run_collection`, writing chunks and a run report, and
storing through `pipelines/store_universal.py` unchanged.

## Decisions this plan fixes

1. **Detection primitives live in `data`.** B29 needs the language facts inside
   `data/enrich.py`, but `data` may not import `processing` (it sits below it).
   `analyze_text_language` and the `processing/language_requirements.py` content
   move to `src/jobscraping/data/language.py`; salary detection moves to
   `src/jobscraping/data/salary.py` because enrichment also needs it without a
   scraper. `processing/attributes.py` and
   `processing/language_requirements.py` become re-export shims for existing
   callers and are removed in B44. No `processing/language.py` is created: the
   only `language.py` is `data/language.py`, and profile language policy stays
   in `profiles/`. User decision, 2026-11-26.
2. **`schema_version` is a per-vault sidecar.** Posting files are dicts keyed by
   identity, so a top-level key would read as a posting. The vault folder carries
   `vault_meta.json` with `{"schema_version": 1, "updated_at": <UTC ISO>}`.
   `collection_scope.json` is deliberately not extended: `same_scope` compares
   the loaded dict, and adding a key would invalidate every existing scope.
   User decision, 2026-11-26.
3. **The neutral diff takes records; only a compatibility wrapper takes paths.**
   `data/compare.py::get_added_and_removed(new, previous)` is pure and injects
   nothing. `processing/postings_utils.py` keeps the same public name with the
   same signature, loads string paths, and delegates, so the legacy callers stay
   untouched (Q16 default). Profile derivation adds its own `points` default and
   ordering so its output does not change.
4. **The grouped non-empty merge rule is split out as B27a.** B27 moves code
   with parity so the B04 fixtures stay the gate unchanged; B27a then applies
   the rule in `artifacts.md` with a deliberate fixture update. This resolves
   the conflict between B27's "tests pass unchanged" and `artifacts.md`'s merge
   rules. The rule is general, not description-only: observed facts need a
   non-empty observation, derived fields are authoritative when present, four
   metadata fields always refresh, and merge-owned dates are computed.
5. **`store_universal.py` becomes orchestration only**: factual projection,
   rebuild, four writes, incomplete-run evidence. All pure logic is in `data/`.
6. **Universal filtering was already absent after M4.** `listings` and `details`
   are filter-free; `_filter_postings` and `_process_data` run only in the legacy
   `gather_data(process=True)` body. B31 therefore verifies that state and adds
   the annotations instead of removing a filter that no longer runs.
7. **UTC applies to new writes only.** `files_io.save_data` timestamps and the
   incomplete-run filename become UTC. Other `datetime.now()` producers
   (`derive_profile_postings`'s migration baseline) are reported, not changed in
   M5.

---

## B26 — `data/load.py`

- **In:** `store_universal.py`, and every caller of `load_postings`.
- **Does:** move `load_postings`; add one thin write wrapper over `files_io`;
  keep `files_io` as the JSON/format layer.
- **Out:** `src/jobscraping/data/load.py` owning relative vault paths, record
  loading and the write entry point.
- **Next:** B27 rebuilds history through it; B30 hardens the same functions.

```python
# src/jobscraping/data/load.py
def load_postings(path, filename) -> dict: ...
def save_json(data, path, filename, *, with_timestamp=False) -> Path: ...
def save_posting_set(records, path, filename) -> Path: ...   # meta added in B30
```

`get_date_of_collection` stays in `processing/postings_utils.py` until B29, where
it moves with `enrich_postings` (its only consumer) into `data/enrich.py`.
`save_incomplete_run` does **not** move: it projects with `factual_postings`, so
it stays in the pipeline module and calls `save_json`.

## B27 — `data/merge.py`

- **In:** `merge_observations`, `_material_changed`, `_last_modified_on`,
  `merge_matched_titlewords`, and the rebuild currently inside
  `store_universal_postings`.
- **Does:** move the merge rules unchanged (including `last_modified_on`) and
  express the rebuild as data in → data out; separate loading/writing stays in
  `data/load.py`.
- **Out:** a pure merge module; `store_universal.py` becomes a four-write
  orchestrator.
- **Next:** B28 replaces the local added-id computation with the neutral diff;
  B29 enriches before this merge; B31 relies on B27a's derived-field rule.

```python
# src/jobscraping/data/merge.py
def merge_matched_titlewords(target_posting, incoming_posting) -> None: ...
def merge_observations(current, previous) -> dict: ...
def rebuild_history(current, previous) -> tuple[dict, dict]:   # (history, added)
    ...

# src/jobscraping/pipelines/store_universal.py
def store_universal_postings(postings, path, scope):
    current = factual_postings(postings)
    previous = factual_postings(load_postings(path, "postings_history.json"))
    history, added = rebuild_history(current, previous)
    save_posting_set(history, path, "postings_history.json")
    save_posting_set(current, path, "current_postings.json")
    save_posting_set(added, path, "newly_added_postings.json")
    save_json(scope, path, "collection_scope.json")
    return current
```

`processing/attributes.py` re-exports `merge_matched_titlewords` for
`split_cached_postings`; `data/merge.py` imports no pipeline, scraper or profile
module. The B04 fixture files and `tests/test_data_rules.py` stay unchanged.

## B27a — non-empty observations win

- **In:** the merged history produced by B27.
- **Does:** replace the blanket observation update with one grouped rule, so a
  field has exactly one merge behaviour.
- **Out:** the merge rules `artifacts.md` states, for every field.
- **Next:** B31's annotations are derived fields and follow the same rule; a
  re-collected posting keeps observed text it did not re-report.

```python
# src/jobscraping/data/merge.py
ALWAYS_FRESH = ("collected_on", "date", "isActive", "url")
DERIVED = ("language", "guessed_required_languages",
           "salary_guessed", "salary_monthly_guessed")
MERGE_OWNED = ("first_collected_on", "last_collected_on", "timespan_days",
               "last_modified_on")
PROVENANCE = ("matched_titlewords",)

def _merged_record(old, posting):
    merged = deepcopy(old)
    for field, value in posting.items():
        if field in MERGE_OWNED or field in PROVENANCE:
            continue
        if field in ALWAYS_FRESH or field in DERIVED:
            merged[field] = deepcopy(value)          # present key is authoritative
        elif _has_value(value):                      # observed fact
            merged[field] = deepcopy(value)
    return merged
```

`_material_changed` follows the same idea: an absent or empty `title` /
`description` is not a change, so `last_modified_on` cannot move for a value the
merge deliberately did not store. The characterization test
`test_empty_later_description_replaces_the_previous_one` becomes
`..._keeps_...`, the fixture record that pins the old result is updated, and new
cases cover an empty scalar, empty list, `False`, `0` and an empty derived value.
No other B04/B02a case changes.

## B28 — `data/compare.py`

- **In:** `get_added_and_removed` and its two callers
  (`processing/derive_profile_postings.py`, `pipelines/collecting.py`).
- **Does:** move the identity diff; delete the `points = 0` injection and the
  `points` ordering; keep path tolerance only in the legacy wrapper. Derivation
  applies its own default and ordering.
- **Out:** a neutral diff that never introduces a profile field.
- **Next:** B33 replaces the derivation wrapper with the data call; B31's
  vault keeps `newly_added` a pure key difference.

```python
# src/jobscraping/data/compare.py
def get_added_and_removed(new: dict, previous: dict) -> tuple[dict, dict]: ...

# src/jobscraping/processing/postings_utils.py
def get_added_and_removed(new, previous):
    return compare.get_added_and_removed(
        load_file_if_str(new, "dict"), load_file_if_str(previous, "dict")
    )

# src/jobscraping/processing/derive_profile_postings.py
for posting in previous_history.values():
    posting.setdefault("points", 0)          # profile's own default
added, removed = get_added_and_removed(candidates, previous_history)
removed = dict(sorted(removed.items(), key=lambda item: item[1]["points"], reverse=True))
```

`store_universal_postings` switches its added-id computation to
`compare.get_added_and_removed(current, previous)[0]`, so one definition remains.
Tests cover added, removed, unchanged and a reappearance (an ID present in
history but absent from the previous current file is not added).

## B29 — `data/enrich.py` and the detection moves

One enrichment segment plus two detection moves.

- **In:** `enrich_postings`, `process_data`'s language step, and the detection
  helpers currently in `processing`.
- **Does:** move language and salary detection down into `data`; move
  `enrich_postings` without the `BaseScraper` import; add an idempotent
  annotation pass; let the annotations survive the fact projection.
- **Out:** enrichment that runs on records with no scraper, no browser and no
  network; `processing` keeps only shims for its old public names.
- **Next:** B31 calls the annotation pass before storage; B33 reads the facts
  instead of recomputing them.

```python
# src/jobscraping/data/language.py        (moved from processing)
LanguageEvidence, extract_language_requirements, guess_required_languages
def analyze_text_language(texts) -> list: ...

# src/jobscraping/data/salary.py          (moved from processing.attributes)
def salary_number_from_str(...): ...
def salary_regex(...): ...
def salary_from_text(...): ...
def salary_from_description(...): ...

# src/jobscraping/data/enrich.py
def annotate_postings(postings, description_key="description") -> dict:
    """Fill language and guessed_required_languages; replace, never merge."""
def get_date_of_collection(value=None, filename=None, overwrite=False) -> str | None: ...  # moved from postings_utils
def enrich_postings(postings, *, overwrite=True, filename=None) -> dict:
    """Salary guesses, collected_on and annotations; no profile reprocessing."""
```

Rules the implementation keeps:

- an annotation is written only for a record with a description;
- a rerun overwrites the same keys and appends nothing, so two runs are
  byte-identical;
- `RAW_POSTING_FIELDS` gains `language` and `guessed_required_languages`, so
  `factual_postings` stops stripping already-annotated records;
- policy reprocessing (`process_data`: filtering, ranking, keywords) does not
  move into `data`; `enrich_postings` has no callers today, so no injection
  parameter is added for it. A future caller composes the two explicitly in
  `processing`.

`processing/attributes.py` imports its public detection names from
`data.language` / `data.salary` (allowed direction) and re-exports them;
`processing/language_requirements.py` becomes the same kind of shim. Both
shims are listed for removal in B44.

## B30 — atomic writes, UTC and the vault sidecar

Two independent parts.

**Part 1 — `io/files_io.py`**

- **In:** every caller of `save_data` and `save_list`.
- **Does:** write to a temporary file in the destination directory and
  `os.replace` it; generate timestamps in UTC; leave reads alone.
- **Out:** a write that cannot truncate an existing artifact.
- **Next:** every later stage inherits write safety.

```python
def save_data(data, path=..., name="", with_timestamp=True, verbose=False) -> None:
    target = ...
    tmp = target.with_name(target.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as file_obj:
        json.dump(...)
    os.replace(tmp, target)
```

**Part 2 — `data/load.py`**

- **In:** the posting-set write wrapper from B26.
- **Does:** write/read a `vault_meta.json` sidecar next to the posting files.
- **Out:** one schema marker per vault folder.
- **Next:** B38/B39 can read the vault version; legacy local-time files still
  read as they are.

```python
# src/jobscraping/config/constants.py
SCHEMA_VERSION = 1
VAULT_META_FILENAME = "vault_meta.json"

# src/jobscraping/data/load.py
def save_posting_set(records, path, filename) -> Path:
    target = save_json(records, path, filename)
    save_vault_meta(path)
    return target

def save_vault_meta(path, updated_at=None) -> Path: ...
def load_vault_meta(path) -> dict: ...        # {} when absent
```

The gate reads "every vault file has `schema_version`" as "every vault folder
has a `vault_meta.json` carrying `schema_version`" (decision 2).

## B31 — store every posting, annotated

- **In:** `run_universal_scrape_flow`'s accepted, quality-checked records.
- **Does:** confirm the universal path runs no relevance/role filter; annotate
  the facts before storage; keep legacy `get_postings` untouched.
- **Out:** universal records with `language`, `guessed_required_languages` and
  `matched_titlewords`, and no profile policy field.
- **Next:** B33 consumes the annotations; B35 selects per profile.

```python
# src/jobscraping/pipelines/scrape_universal.py
raw = factual_postings(result["records"])
...
validate_postings_quality(raw, ...)
raw = annotate_postings(raw)                 # B29's function; enrichment before store
return store_universal_postings(raw, path, scope)
```

Merge treatment: `language` and `guessed_required_languages` are derived fields
under B27a's rule — a present key replaces, even when empty — and are never
unioned. Observed facts keep their stored value when an observation omits them.
`matched_titlewords` keeps its ordered union. No new merge code is expected in
B31; a test pins the annotation replacement.

Tests: a manager/irrelevant fixture is stored in universal, the same record is
rejected by the Dani candidate filter, the stored record passes
`UNIVERSAL_POSTINGS.check`, and no policy field appears.

---

## The milestone end to end

```text
run_universal_scrape_flow(path, …)                                   (B24)
  -> run_collection -> factual_postings                              (M4)
  -> validate_postings_quality                                       (B21)
  -> annotate_postings(raw)                                          (B29/B31)
  -> store_universal_postings(raw, path, scope)                      (B27)
       load_postings(history)                                        (B26)
       rebuild_history -> history + added                            (B27/B28)
       save_posting_set x3 + save_json(scope) + vault_meta.json      (B26/B30)
  -> vault: current / history / newly-added / scope / meta

legacy: get_postings -> get_added_and_removed wrapper -> compare     (B28)
        derive_profile_postings -> merge_observations                (B27)
```

## Gates for the milestone

- `uv run python -m unittest discover -s tests` → `OK`; report the printed
  count. The WIP modules (`test_dani_profile.py`, `test_language_requirements.py`,
  `test_raw_collection.py`) stay green.
- `rg "def load_postings|def merge_observations|def get_added_and_removed" src/jobscraping/pipelines` → none.
- `rg "from jobscraping.scrapers" src/jobscraping/processing` → none.
- `rg "jobscraping.pipelines" src/jobscraping/data` → none.
- `rg "jobscraping.processing" src/jobscraping/data` → none.
- `rg "points" src/jobscraping/data` → none.
- `rg "[A-Za-z]:[\\/]|/home/|/Users/" src tests` → none.
- A repeated fixture run writes byte-identical `postings_history.json`.
- A simulated `os.replace` failure leaves the previous file intact.
- Every universal write leaves `vault_meta.json` with `schema_version`.
- New code in B26–B31 passes `uvx ruff check` and `uvx ty check`; findings in
  code the tickets only move are reported, not fixed. "Too many arguments" is
  raised with the user, never silenced.
- Ticket status rows in [tickets/README.md](../README.md) updated in the same
  change as each ticket. Work stays in the working tree.

## Document updates made with this plan

- [module-seams.md](../../design/module-seams.md): `data/language.py` and
  `data/salary.py` in the target map; the detection/policy split; dependency
  note that `data` imports no `processing`.
- [artifacts.md](../../design/artifacts.md): `vault_meta.json` as the
  `schema_version` carrier; the merge rules become the grouped non-empty rule
  applied in B27a.
- [backlog.md](../../backlog.md): B27a inserted; B29 and B30 file lists and
  checks updated.
- [tickets/README.md](../README.md): B27a row and the M5 status table.
