# Specs and dataclasses

Status: decided 2026-11-16; refined 2026-11-24 with Q29 (profile-neutral
annotations in the universal record). Field sets follow the current pipeline's
logic; they are the minimum contracts the refactoring moves behavior onto.

The contract that matters is the **data spec** for each pipeline step, not a
dataclass per helper object. Most of the earlier dataclass candidates were too
fine-grained and are dropped or merged. One question is still open in
[open-questions.md](open-questions.md): the compatibility layer (Q16).

## Specs versus configs

Keep these terms separate:

| Term | Meaning | Lives in | Serialized |
| --- | --- | --- | --- |
| **Data spec** | The shape of the records at a step: key, important fields, which step produces them. | code (`specs/`) | no |
| **Collection config** | What to collect: sites, queries, locations, enabled steps, overrides. | `conf/` YAML → dataclass | yes, as YAML |
| **Profile config** | Per-profile tunables: threshold, salary floor, locations, scoring values, language values, outputs. | `conf/` YAML → dataclass | yes, as YAML |

A data spec is a contract and belongs in code. Collection and profile config are
operations input and belong in `conf/`. Do not put field definitions in YAML and
do not put tunable values in code specs.

## Where specs live

```text
src/jobscraping/specs/
  base.py               # FieldSpec, DataSpec, check
  postings.py           # DISCOVERED_POSTINGS, COLLECTED_POSTINGS, UNIVERSAL_POSTINGS,
                        # SCORED_POSTINGS, SELECTED_POSTINGS
  companies.py          # only when a real side export exists
```

Specs are imported by adapters, data functions and profiles, so they live below
all of them in the dependency graph. They are not in `conf/`:

- the code reads field names at import time, and a spec is not run-tunable;
- a malformed YAML spec would fail at runtime instead of review time;
- a spec change is a code review because processing depends on the names.

What *is* config: which columns an export includes, completeness thresholds per
source, and the query list. See [Q6 and Q20](open-questions.md#resolved-questions).

## Data specs

### Shape

```python
@dataclass(frozen=True)
class FieldSpec:
    name: str
    kind: str                       # str | int | float | bool | date | list | dict | any
    required: bool = False
    produced_by: str | None = None  # step that fills it
    note: str = ""

@dataclass(frozen=True)
class DataSpec:
    name: str
    key: tuple[str, ...]
    fields: tuple[FieldSpec, ...]

    def extend(self, *fields: FieldSpec) -> "DataSpec": ...
    def check(self, records: dict[str, dict]) -> list[str]: ...
```

Rules:

- Only the fields that processing actually relies on are declared. The universal
  record still keeps every key it receives, including unknown ones.
- Unknown fields are allowed and never removed. This is what lets a JSON export
  remain a dict and lets older data flow through newer code.
- `check` reports problems; it does not mutate or coerce.
- Records are still dicts keyed by identity. A typed record class is not
  required; if one is ever useful, it is a view at one boundary, not the
  universal record type. A record dataclass must convert back to a dict before
  storage and must not become a second schema.
- Required fields are identity and location of the record, not the full
  downstream shape. Completeness of title, company, description and dates is a
  quality-gate setting per source, because sites differ. This is the Q3 answer:
  specs follow current pipeline logic, and no adapter-specific spec variant is
  needed.

### Specs per step

Field names match the current code (`RAW_POSTING_FIELDS`, derivation keys,
scored keys). A column marked *required* fails the check; *expected* is checked
by the quality gate with per-source thresholds; the rest is optional.

| Spec | Key | Required | Expected / optional | Consumed by |
| --- | --- | --- | --- | --- |
| `DISCOVERED_POSTINGS` | `source`, `id` | `source`, `id`, `url` | `title`, `company`, `locations`, `collected_on`, `date`, `isActive` | listing step, detail steps |
| `COLLECTED_POSTINGS` | `source`, `id` | `source`, `id`, `url` | `title`, `company`, `description`, `collected_on`, `date`, `salary`, `salary_guessed`, `salary_monthly_guessed`, `locations`, `isActive`, `isHomeOffice`, `employmentTypes`, `snippet`, `role`, `requirements`, `nice_to_have`, `benefits` | quality gate, universal storage |
| `UNIVERSAL_POSTINGS` | `source`, `id` | `source`, `id`, `url` | `first_collected_on`, `last_collected_on`, `timespan_days`, and every other `RAW_POSTING_FIELDS` key, including title, company, description, dates, salary and `matched_titlewords`; plus the profile-neutral annotations `language` and `guessed_required_languages` | derivation, history |
| `SCORED_POSTINGS` | `source`, `id` | `source`, `id`, `points` | carried from universal: `language`, `matched_titlewords`, `guessed_required_languages`; produced by derivation: `keywords`, `role_families`, `language_adjustment`, `language_excluded`, `profile_excluded` | selection, outputs |
| `SELECTED_POSTINGS` | `source`, `id` | `source`, `id`, `points` | same fields as scored | outputs |

`SELECTED_POSTINGS` is a subset of `SCORED_POSTINGS`, not a new shape.
`UNIVERSAL_POSTINGS` has no **profile policy** fields: `points`, `keywords`,
`role_families`, `language_adjustment`, `language_excluded` and
`profile_excluded` are produced by derivation and never enter the vault.
Old profile points are dropped when backfilling (Q14, plan only).

### Profile-neutral annotations

Not every derived field is profile policy. A field belongs in the universal
record when any profile would compute the same value from the record and
non-profile config (Q29). Today that is:

| Field | Producer | Why it is not policy |
| --- | --- | --- |
| `matched_titlewords` | collection | Which query titleword found the posting; already collection-owned. |
| `language` | `data/enrich.py` | Detected description language; `analyze_text_language` reads the text only. |
| `guessed_required_languages` | `data/enrich.py` | Deterministic `guess_required_languages` evidence from the description. |

The profile still owns what it *does* with them: `language_adjustment`,
`language_excluded`, `profile_excluded`, `points`, `role_families` and the
`keywords` vocabulary are policy and stay in scored/selected.

`keywords` is deliberately not universal: the occurrence list is factual given a
vocabulary, but that vocabulary is `description_keywords_order`, a profile
setting. If a collection-level keyword list is ever defined in `conf/`, keywords
could move too; that is not this decision.

Test for the boundary: adding a second profile with a different vocabulary,
threshold or language policy must not change any field the universal record
holds.

Code follows the decision in B07a: until it lands, `language` and
`guessed_required_languages` are declared only in `SCORED_POSTINGS`.

Side outputs (a company list, for example) get their own spec only when a real
export exists. They are exports or BI views, not pipeline datasets (Q18).

### Passing data and spec

A step receives the records and the collection config, and returns new records
that satisfy its output spec. The caller binds the input spec and checks the
data against it; the step itself does not take the spec for its own data:

```python
def details(records: dict, config: CollectionConfig) -> dict:
    # the caller has already checked records against DISCOVERED_POSTINGS
    ...
    enriched = {key: {**record, "description": ...} for key, record in records.items()}
    return enriched                  # validated against COLLECTED_POSTINGS
```

The caller rebinds: `records = step.run(records, config)`. A step does not mutate
the shared dict in place (Q22).

This is what makes a step startable from the middle of the pipeline:

1. Load the saved artifact for the step's input.
2. Load the input spec.
3. Check the data against it.
4. Run the step.
5. Check the result against the output spec; write.

The input is supplied by the caller (a pipeline node, a catalog dataset, a test),
not discovered by the step. No stage assumes that one universal history exists or
is current (Q28).

A missing required field is a failed start, not a silent empty result. A missing
expected field lowers completeness and may fail the quality gate; a missing
optional field is allowed.

Specs themselves are not saved. The saved JSON plus the spec constant is enough
to reconstruct the contract. There is no spec digest or spec version in
artifacts (Q27); a vault-level `schema_version` is enough. If a spec changes,
the check reports what old data lacks; no migration is needed for added optional
fields.

A step does not return its spec. The step declaration names its output spec, and
the collector validates the returned records against it. This keeps the spec one
thing per step rather than something each implementation can redefine.

## Dataclasses that remain

| Candidate | Decision | Why |
| --- | --- | --- |
| `FieldSpec`, `DataSpec` | **Yes** | The step contract; the thing that lets a stage start from saved data. |
| `CollectionConfig` | **Yes** | Merges the old `ScrapeScope` and `CollectionRequest`. Built from YAML; `scope_digest()` supplies cache validity. |
| `ProfileConfig` | **Yes** | Built from YAML. Absorbs the earlier `ScoringConfig` and language values. |
| `Step` | **Optional convenience** | Adapters declare ordered steps in their own module. A small frozen dataclass (name, optional specs, callable) is allowed; no enforcement machinery. |
| `ProfilePolicy` | **No** | Plain functions plus `ProfileConfig` (Q5). |
| `StepReport` / `RunReport` | **JSON for now** | The collector writes a JSON run report; a dataclass waits for a second consumer (Q25). |
| `DerivationResult` | **Defer** | The current dict (`results`, `added`, `removed`, `companies`) is adequate. |
| `QualityPolicy` / `QualityReport` | **No dataclass** | The gate's rules are ordinary arguments and YAML values. |
| `ArtifactPaths` | **Dropped** | Paths are relative inputs from the pipeline/catalog, not a domain object. |
| `LanguagePolicy` | **Dropped as a dataclass** | Language values live in `ProfileConfig.language`; `LanguageEvidence` (existing frozen dataclass) remains the seam between evidence and policy. |
| `Posting` | **Not now** | JSON export implies dicts. Dataclasses may model related data, but the record stays a dict; do not enforce the existing schema. |

### `CollectionConfig`

```python
@dataclass(frozen=True)
class CollectionConfig:
    sites: tuple[str, ...]                 # adapter names
    queries: tuple[str, ...]
    locations: tuple[str, ...] = ()
    steps: tuple[str, ...] = ()            # empty = every adapter's default
    overrides: Mapping[str, object] = field(default_factory=dict)
    cache_mode: str | None = None
    cached_postings: Mapping[str, dict] = field(default_factory=dict)
    cache_hit_predicate: Callable[[str, dict, dict | None], bool] | None = None

    def scope_digest(self) -> str: ...     # sites, queries, locations, steps, overrides
```

`cached_postings` and `cache_hit_predicate` are run inputs, not scope: a details
step reads them to skip work for reusable IDs, and they are excluded from
`scope_digest()` so cache contents never change a scope. The four scope fields
and `overrides` are the digest's whole input, as before. This pair is the
current minimum, not a final shape: the caching logic may later become an
arbitrary supplied callable and may become site-scoped (Q31).

Why it is one object: a collection run is one YAML block. Splitting "scope" from
"request" made `sites` appear twice and added a second object with no separate
consumer. The digest is a method, not a saved file shape; the YAML config plus
the digest may make the current `collection_scope.json` artifact redundant.
`CollectionConfig` is the final name (Q21, Q26).

### `ProfileConfig`

```python
@dataclass(frozen=True)
class ProfileConfig:
    name: str
    threshold: float = 0.01
    salary_bearable: int = 4100
    locations_primary: tuple[str, ...] = ()
    locations_secondary: tuple[str, ...] = ()
    scoring: Mapping[str, float] = field(default_factory=dict)
    language: Mapping[str, object] = field(default_factory=dict)
    outputs: Mapping[str, object] = field(default_factory=dict)
```

This absorbs the earlier `ScoringConfig` and `LanguagePolicy`. It is deliberately
one YAML-backed object per profile. Scoring stays values, not a class (Q4): all
profiles use the same `rank_postings` shape with different dictionaries. If a
profile later needs pre/post behavior, that is a new decision.

## When a dataclass earns its place now

A dataclass is justified when it is:

1. a **data spec** (the step contract), or
2. a **YAML-backed config** built at a boundary, or
3. a **result** with two or more consumers that need structured access.

It is not justified when it renames arguments, mirrors a JSON record, groups
unrelated values, or exists for only one caller. This is the explicit answer to
"too many dataclasses".
