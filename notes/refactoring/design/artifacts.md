# Artifacts

Status: decided 2026-11-16 for paths, failure behavior and write safety. Paths
and names below are relative to a repository root derived from `__file__`; no
committed path is absolute. Exact names may still change when Kedro's catalog
pins them.

Artifacts are the interface between stages. A stage is startable when its inputs
exist on disk and its outputs are named; anything else is an implementation
detail. This document fixes names, ownership and merge semantics before Kedro's
catalog pins them.

## Current artifacts (verified 2026-11-16)

Universal, under `data/save/postings/universal/`:

| File | Producer | Meaning |
| --- | --- | --- |
| `current_postings.json` | `store_universal_postings` | facts from the latest accepted collection |
| `postings_history.json` | `store_universal_postings` | merged observations over time; also the factual cache |
| `newly_added_postings.json` | `store_universal_postings` | IDs absent from the previous universal history |
| `collection_scope.json` | `store_universal_postings` | normalized scope of the last run; equality enables cache reuse |
| `vault_meta.json` | `data/load.py` | `{schema_version, updated_at}`; the vault's schema marker, rewritten with every posting write |
| `incomplete_run_<timestamp>.json` | `save_incomplete_run` | `{error, postings}` from a rejected quality gate; new filenames use UTC |
| `collections/dani/*` | `pipelines/dani.py` | a scoped collection whose provenance must not replace the root vault |

Profile, under `data/save/postings/<profile>/`:

| File | Producer | Meaning |
| --- | --- | --- |
| `postings_history.json` | derivation | all candidates seen, with scores |
| `current_postings.json` | derivation | candidates or selected postings depending on `only_thresholded_stored` |
| `newly_added_postings.json` | derivation | candidates absent from the pre-merge profile history |
| `newly_added_history.md` | `log_to_markdown` | human-readable log |
| `migration_baseline_<date>.json` | derivation | one-time copy of the previous history before a migration run |
| `postings_<timestamp>.json` | derivation, `efficient_storing=False` | debugging dump of all candidates |

Other outputs: `data/save/excels/`, `data/save/companies/`, plus legacy
`*_.json` filenames that still appear in local data but are not written by the
current code.

## What is not an artifact

- **Data specs.** They are code constants (`specs/postings.py`), not files. An
  artifact plus its spec reconstructs the contract; nothing spec-shaped is
  written per run.
- **Collection and profile config.** They are `conf/` YAML, loaded into config
  objects at the pipeline boundary. They are not pipeline outputs.
- **A separate paths object.** Paths are supplied by the catalog/pipeline; there
  is no `ArtifactPaths` dataclass.

## Collection steps and partial results

- A chunk is written per completed step/unit, not per whole run. The chunk
  carries the step name and the data it produced.
- A skipped step produces no chunk. The absence is information: the next stage's
  input spec decides whether the data is usable.
- A failed step writes its failure to the JSON run report; chunks already
  written by earlier steps remain valid.
- A unit with zero records is a failed acquisition and contributes to the
  acquisition gate; it does not write an empty chunk.
- Side outputs such as company lists are exports or BI views, not pipeline
  datasets; they are not part of the vault (Q18).
- `current_postings.json` is overwritten after a successful profile run. There
  is no per-unit gating of the profile current file (Q24); partial acquisition
  data is visible in history and the run report.

## Ownership

| Artifact | Owner | Consumers |
| --- | --- | --- |
| raw chunks | acquisition | universal storage |
| universal current/history/newly-added/scope | data + collection pipeline | derivation, outputs |
| incomplete-run artifact | acquisition quality gate | humans, pipeline failure handling |
| profile history/candidates/current/newly-added | profile derivation | outputs, next derivation |
| Excel, Markdown, email | outputs | humans |
| baseline and debug dumps | migration tooling | humans |

No profile writes to the universal folder. No universal stage reads a profile
folder. The Dani scoped collection writes under its own `collections/dani/`
folder precisely so it cannot be mistaken for root coverage.

The universal folder is the expected layout, not a contract that every run
produces. Derivation receives its input records from the caller (a pipeline node,
a catalog dataset or a test) and does not discover or require a universal
history; a run can be planned per pipeline as today (Q28).

### History as the source of truth

`postings_history.json` is the only universal file that carries facts.
`current_postings.json` is the latest observation per ID, `newly_added_postings.json`
is an ID-set difference against the previous history, and the scope file marks a
run; all three are views over history. The user may later default universal
storage to history only (Q32), so:

- a merge must be able to write history alone, and a reader must be able to
  start from history and produce current in memory;
- no fact may exist only in current, newly-added or the scope file — if it is
  not in history, it cannot be recovered after the run;
- consumers take records, never "the current file" by name (Q28), so switching
  the default input from current to history is a pipeline wiring change.

## Merge and diff rules

These are the rules the current code implements or intends; they must be
fixtures before the data layer moves.

- **Identity.** `source + id` (for example `karriere.at7818416`). A new source
  must not reuse an existing prefix.
- **Dates.** `first_collected_on` = earliest known, `last_collected_on` = latest
  known, `timespan_days` recomputed from those two. `collected_on` is the
  observation date and is not a range.
- **Material change.** `last_modified_on` is the observation date on which the
  posting's material last changed. Only `title` and `description` decide a
  change, compared as the raw values the observation supplies. An absent or
  empty value is not a change, because the merge does not store it. No other
  field does: `isActive`, the site's `date`, `url`, locations, salaries and the
  merge bookkeeping (`collected_on`, `first_collected_on`, `last_collected_on`,
  `timespan_days`) are ignored, and the comparison ignores `last_modified_on`
  itself so a repeated merge cannot move it.
- **Missing values.** Only fields present in the observation are compared; an
  absent `title`/`description` leaves the stored value in place and is not a
  change. Missing and empty compare equal, so an empty observation of a record
  that also has no value is not a change.
- **First observation and legacy records.** A record with no stored facts gets
  `last_modified_on = collected_on` of that observation, so the field is never
  `None` on a new record. A stored record that predates the field and whose
  material is unchanged takes its `last_collected_on` (falling back to
  `collected_on`) as the last known change date. A record whose observations
  carry no date at all has no value to resolve: the merge omits the field
  rather than inventing one. Any record with at least one dated observation
  carries the field.
- **One owner, no backfill.** Only the merge computes `last_modified_on`;
  adapters, enrichment and derivation never set it. Existing history is not
  backfilled (Q27): old records gain the field on their next observation.
- **Description.** Follows the observed-facts rule below. The blanket
  `{**old, **posting}` merge currently lets a later empty description replace a
  stored non-empty one; B27 moves the merge with parity so the B04 fixtures pass
  unchanged, and B27a applies the grouped rule and updates the one fixture that
  pins the old result.
- **Observed facts.** A non-empty observation replaces the stored value; an
  absent, `""`, `None`, `[]` or `{}` value leaves the stored one in place.
  `False` and `0` count as values and replace. This applies to every field the
  collector observes and the merge does not own, including `title`, `company`,
  `description`, `salary`, `locations`, `isHomeOffice`, `employmentTypes`,
  `snippet`, `role`, `requirements`, `nice_to_have` and `benefits`. A site that
  temporarily omits a field never erases a stored fact.
- **Derived fields.** `language`, `guessed_required_languages`,
  `salary_guessed` and `salary_monthly_guessed` are recomputed from the latest
  observation and are authoritative: a present value replaces the stored one
  even when the recomputation is empty or `None`. An absent key leaves the
  stored value untouched.
- **Always fresh.** `collected_on`, `date`, `isActive` and `url` always come
  from the observation (the same set `split_cached_postings` treats as fresh).
- **Merge-owned fields.** `first_collected_on`, `last_collected_on`,
  `timespan_days` and `last_modified_on` are computed by the merge and never
  taken from the observation.
- **Lists.** Observed list fields replace when non-empty; an empty list leaves
  the stored one. `matched_titlewords` is the exception and accumulates
  provenance by ordered union.
- **Vocabulary of a fact.** An empty value means "the observation did not
  report it", not "the site erased it"; there is no deletion signal in the
  vault. A field is removed only by a deliberate schema change, never by an
  empty observation.
- **Profile policy fields.** `points`, profile keywords, `role_families`,
  `language_adjustment`, `profile_excluded`, `language_excluded` and profile
  scores never enter universal records.
- **Profile-neutral annotations.** `language` and `guessed_required_languages`
  are universal fields (Q29) and derived fields under this rule: they are
  replaced by the latest enrichment, even when the recomputation is empty or
  `None`, and never unioned. `matched_titlewords` stays a collection field and
  unions.
- **Vocabulary.** "Universal" names the expected shared record shape and folder,
  not a run that must exist. Interfaces that read or write it take records or
  paths as arguments; no stage or profile discovers a universal history (Q28).
- **Diff.** Added = keys in current, absent from previous. Removed = keys in
  previous, absent from current. The neutral diff must not inject `points` or
  any other profile default.
- **Reappearance.** A known posting that reappears is current, not newly added.
  A score-only change is not newly added. This is confirmed Dani behaviour and
  the intended generic rule.

## Resume and failure

- **Scope digest.** `CollectionConfig.scope_digest()` over sites, queries,
  locations, steps and overrides decides whether a previous snapshot may serve
  as a retention baseline. A different digest must not silently overwrite root
  coverage.
- **Chunks.** One chunk per completed site/query/location/step unit. A rerun
  with the same digest reuses valid chunks. A skipped step has no chunk. Proposed
  layout:

  ```text
  data/save/postings/universal/chunks/<scope-digest>/<source>/<query-slug>/<step>/<unit>.json
  ```

  The digest is a hash of the normalized collection config; the slug is a
  readable derivative, not an identity. Exact naming is open.

  In M4 (B23) a unit is one adapter: its `listings` step owns the
  query×location loops, and `Step.run` receives no unit argument. The chunk is
  therefore `chunks/<scope-digest>/<source>/<step>.json`, one file per completed
  step. Per-query chunks wait for a step-level unit argument; that is a later
  change, not a silent omission. The chunk file is
  `{"source", "step", "records"}` so the step name survives a path rename.
- **Partial failure.** A failed quality gate writes one
  `incomplete_run_<timestamp>.json` and raises; current/history files are not
  touched. Acquisition failure is never reported as "no relevant postings".
- **Partial units.** A unit that fails after retries is recorded as a failure,
  not as an empty chunk. Empty and failed are different states.
- **Write safety.** Decided: write to a temporary file in the same directory and
  `os.replace` it (Q12). Never open the destination with `"w"`. `save_data`
  currently writes in place; it is the first data-layer change.
- **Time.** Decided: UTC for all new artifacts and filenames (Q13). Existing
  local-time files are read as they are; no conversion is attempted.
- **Schema version.** Decided: a `schema_version` field on vault artifacts
  (Q13). Posting files are dicts keyed by identity, so the version is carried by
  a per-folder `vault_meta.json` (`{schema_version, updated_at}`) written by
  `data/load.py`; a top-level key in a posting file would read as a posting. The
  scope file is not extended, because its equality decides cache reuse. There is
  no per-spec version or digest and no requirement to keep old data compatible
  (Q27); a spec change is handled by the check, not by migration.
- **Run report.** Decided: JSON artifact written by the collector (Q25),
  including unit, step, outcome and error. Promote to a dataclass only when a
  second consumer needs structured access. In M4 it is `<vault>/run_report.json`,
  rewritten by each run of that scope (B23).

## Stage interface

| Stage | Reads | Writes | Resume key |
| --- | --- | --- | --- |
| collect | `CollectionConfig`, optional seed history | chunks, run report, incomplete-run on failure | scope digest + unit + step |
| store universal | chunks or facts, previous universal files | universal current/history/newly-added/scope (history-only is a later option, Q32) | scope digest |
| derive profile | **input records supplied by the caller** (in practice the universal current file), `ProfileConfig`, profile functions, profile history | profile candidates/history/current/newly-added/baseline | profile name |
| outputs | profile current/newly-added | Excel, Markdown, email | profile + run date |

A policy change makes a derivation rerun a new derivation, not a continuation.
There is no stored policy version (Q27); rerun deliberately and compare the
artifacts.

## Backfill artifacts

Backfilling the universal vault from existing profile histories is a separate,
reviewable operation:

1. `backfill_dry_run_<date>.json`: counts per profile, unique IDs, overlaps,
   conflict examples, fields that would be dropped.
2. Human review of the dry run.
3. Write to a new folder, not over the existing vault, and swap deliberately.

The dry run is the point: `data/save/postings/universal/` already contains
history with broader or different coverage than a single profile run.

## Decided details and remaining implementation choices

Decided: UTC and `schema_version` (Q13); atomic writes (Q12); JSON run report
(Q25); overwrite profile current (Q24); chunks per site/query/location/step
(Q11); no spec digest and no old-data compatibility (Q27).

Still implementation details, decided during Phase 4:

- exact chunk filename format inside the `<scope-digest>/<source>/<query>/<step>`
  path;
- whether `collection_scope.json` remains once the YAML config plus
  `scope_digest()` is authoritative (keep it until the catalog replaces it);
- whether `migration_baseline_*` and `postings_<timestamp>.json` survive;
- one vault file per state or a partitioned store, if file size ever matters.

The only design question still open is Q16, the compatibility layer. See
[open-questions.md](open-questions.md#still-open).
