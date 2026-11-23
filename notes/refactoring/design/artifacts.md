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
| `incomplete_run_<timestamp>.json` | `save_incomplete_run` | `{error, postings}` from a rejected quality gate |
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

## Merge and diff rules

These are the rules the current code implements or intends; they must be
fixtures before the data layer moves.

- **Identity.** `source + id` (for example `karriere.at7818416`). A new source
  must not reuse an existing prefix.
- **Dates.** `first_collected_on` = earliest known, `last_collected_on` = latest
  known, `timespan_days` recomputed from those two. `collected_on` is the
  observation date and is not a range.
- **Description.** Latest non-empty observation wins.
- **Scalars.** An existing non-empty value is preserved; a new non-empty value
  fills a missing one. Conflicts are resolved by an explicit rule, not by dict
  order.
- **Lists.** Ordered union; `matched_titlewords` accumulates provenance.
- **Profile fields.** `points`, profile keywords, `profile_excluded`,
  `language_excluded` and profile scores never enter universal records.
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
  (Q13). Added when the data layer is extracted. There is no per-spec version or
  digest and no requirement to keep old data compatible (Q27); a spec change is
  handled by the check, not by migration.
- **Run report.** Decided: JSON artifact written by the collector (Q25),
  including unit, step, outcome and error. Promote to a dataclass only when a
  second consumer needs structured access.

## Stage interface

| Stage | Reads | Writes | Resume key |
| --- | --- | --- | --- |
| collect | `CollectionConfig`, optional seed history | chunks, run report, incomplete-run on failure | scope digest + unit + step |
| store universal | chunks or facts, previous universal files | universal current/history/newly-added/scope | scope digest |
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
