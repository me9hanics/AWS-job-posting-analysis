# M2 implementation flow — data specs and the step contract

The milestone's own view of what B06–B10 build and where each piece sits. Tickets
run in order; each gets its own short chain, with the mock shapes it introduces.
Mock code shows boundaries only — it is never imported or copied verbatim.

`In → Does → Out → Next`, per ticket. A ticket with unrelated parts gets one
chain per part; a ticket that builds one continuous segment gets one chain.

---

## B06 — the `specs` package

Two types, no runtime flow yet. This is the "part 1" the rest of the milestone
hands around.

- **In:** nothing at import; stdlib only.
- **Does:** define the two frozen types, `extend` (new spec) and `check`
  (report problems, never coerce).
- **Out:** `FieldSpec`, `DataSpec`.
- **Next:** B07 fills constants; B09 annotates steps; B08 fixes the rules in
  tests.

```python
@dataclass(frozen=True)
class FieldSpec:
    name: str
    kind: str                       # str | int | float | bool | date | list | dict | any
    required: bool = False
    produced_by: str | None = None
    note: str = ""

@dataclass(frozen=True)
class DataSpec:
    name: str
    key: tuple[str, ...]            # identity field names; the dict key is the caller's
    fields: tuple[FieldSpec, ...]

    def extend(self, *fields: FieldSpec) -> "DataSpec": ...
    def check(self, records: dict[str, dict]) -> list[str]: ...
```

---

## B07 — the five posting specs

One data flow: vocabulary in, five constants out.

- **In:** `FieldSpec`/`DataSpec` (B06), the field names already in
  `RAW_POSTING_FIELDS`, the universal store and derivation.
- **Does:** declare five specs; required = `source`, `id`, `url`
  (`points` added for scored/selected); universal carries every raw key and no
  profile key.
- **Out:** `DISCOVERED_POSTINGS`, `COLLECTED_POSTINGS`, `UNIVERSAL_POSTINGS`,
  `SCORED_POSTINGS`, `SELECTED_POSTINGS`.
- **Next:** B09 binds them to steps; B22 checks step boundaries; B31 stores the
  universal shape.

The shapes differ only in which fields each stage owns (`*` = required):

```python
DISCOVERED_POSTINGS  # source*, id*, url* | title, company, locations, collected_on, date, isActive
COLLECTED_POSTINGS   # + description, salary, salary_guessed, salary_monthly_guessed,
                     #   isHomeOffice, employmentTypes, snippet, role, requirements,
                     #   nice_to_have, benefits
UNIVERSAL_POSTINGS   # every RAW_POSTING_FIELDS key + first/last_collected_on,
                     #   timespan_days, last_modified_on  (no points/keywords/language)
SCORED_POSTINGS      # source*, id*, points* | language, matched_titlewords, keywords,
                     #   role_families, guessed_required_languages,
                     #   language_adjustment, language_excluded, profile_excluded
SELECTED_POSTINGS    # same fields as SCORED_POSTINGS, filtered subset
```

---

## B08 — the spec contract tests

- **In:** the specs (B06/B07) and hand-written fixture records.
- **Does:** assert the four rules: missing required is reported by name; unknown
  keys pass and stay; `extend` returns a new spec; `check` neither mutates nor
  coerces.
- **Out:** `tests/test_specs.py`.
- **Next:** every later adapter, collector and stage can trust `check`; B22
  copies the "problems are a failed start" reading.

```python
DISCOVERED_POSTINGS.check({"karriere.at1": {"source": "karriere.at", "id": "1"}})
# -> ["karriere.at1: missing required field 'url'"]
```

---

## B09 — the adapter step contract

- **In:** `DataSpec` (B06) and a site module's own step functions.
- **Does:** declare a step as name + callable + optional specs; allow plain
  `(name, callable)` pairs; no enforcement.
- **Out:** `Step`, `SiteAdapter`, `CollectionConfigLike` (the config slice a step
  may read until B32).
- **Next:** B10 proves the shapes; B19/B20 declare real adapters; B22 runs them.

```python
RecordSet = dict[str, dict]

@dataclass(frozen=True)
class Step:
    name: str
    run: Callable[[RecordSet, CollectionConfigLike], RecordSet]
    input_spec: DataSpec | None = None
    output_spec: DataSpec | None = None

class SiteAdapter(Protocol):
    source: str
    steps: tuple[Step | tuple[str, StepRun], ...]   # declared order

# what a site module will look like (B19/B20):
class KarriereAT:
    source = "karriere.at"
    steps = (
        Step("listings", LISTINGS, output_spec=DISCOVERED_POSTINGS),
        Step("details", DETAILS, input_spec=DISCOVERED_POSTINGS,
             output_spec=COLLECTED_POSTINGS),
    )
```

---

## B10 — proving the contract with fake adapters

Two fake site shapes and a test-local runner. This chain is the one B22 copies.

- **In:** `Step`/`SiteAdapter` (B09) and fake record dicts.
- **Does:** iterate declared steps in order; skip by name; catch a raising step
  and keep going; flag zero records.
- **Out:** a report per adapter and the final record set.
- **Next:** B22 replaces the test runner with the collector but keeps the call
  shape and the report fields.

```python
run_steps(adapter, records, config=None, only=None)
# -> {"source": str, "steps": [{"name", "status", "records"|"error"}],
#     "failed": bool, "records": RecordSet}

run_steps(FailingDetails, {})
# steps: [("listings", "ok"), ("details", "failed"), ("cleanup", "ok")]
# failed: True, records: still the listing result
```

---

## The milestone end to end

After B06–B10 the whole contract exists but nothing runs it in production:

```text
adapter declares steps + specs (B09)
  -> caller checks input spec (B06 check)
  -> step runs (records, config) -> records
  -> caller checks output spec
  -> artifact JSON + code spec constant (B31)
  -> next stage loads and re-checks its own input spec (B36)
```

What is fixed in place: field vocabulary from `RAW_POSTING_FIELDS`; required
fields = identity + URL (plus `points` after derivation); no profile fields in
the universal shape; `check` reports, never coerces; specs travel beside the
callable, not inside it.
