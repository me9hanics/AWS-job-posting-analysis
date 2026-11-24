# Migration workstream

Status: decided direction 2026-11-16. Baseline recorded 2026-11-23; cutover
per profile is not scheduled.

Owns the order in which parts move, what must be proven before a consumer
switches, which compatibility code may exist temporarily, and what gets removed.

This document condenses [process_map.md](../process_map.md); the process map
remains the detailed reference. Where they disagree, the process map's open
questions win until a decision is recorded here.

## Baseline (recorded 2026-11-23)

Checked against the working tree on 2026-11-23. The suite count is B02's; this
section records command and behaviour, not the pass number. Paths below are
relative to the repository root.

### Live entry points

No script launches another script. The tests do import
`schedule.tech_collect`, `legal_collect`, `tn_collect` and `dani_collect`
directly; otherwise each script runs under `if __name__ == "__main__"`, and the
scheduler and shell history live outside the repository.

| Entry point | Tracked | What it calls |
| --- | --- | --- |
| `schedule/tech_collect.py` | yes | `pipelines.collecting.get_postings` (line 41), then `io.outputs.generate_outputs` and `log_to_markdown`; writes `data/save/postings/tech/` and `data/save/excels/excel_tech/`. |
| `schedule/legal_collect.py` | no (Git-ignored) | Same legacy path (call at line 452); writes `postings/legal/` and `excels/excel_legal/`. |
| `schedule/tn_collect.py` | no (Git-ignored) | Same legacy path (call at line 314); writes `postings/tn/` and `excels/excel_tn/`; inherits `first_collected_on` from `postings/tech/` and `postings/legal/`. |
| `schedule/dani_collect.py` | no (Git-ignored) | `pipelines.dani.collect_dani_postings` imported as `get_postings` (line 10, call line 81), which runs `pipelines.scrape_universal.run_universal_scrape_flow` then `processing.derive_profile_postings.derive_profile_postings`; uses `profiles.dani` constants; writes `postings/dani/`. `pipelines/dani.py` and `profiles/` are untracked work-in-progress, so the Dani path is live but uncommitted. |
| `schedule/hardverapro_collect.py` | no (Git-ignored) | `scrapers.websites.hardverapro.Hardverapro`, which does not exist. Archive-only; see below. |
| `schedule/tech_filter.py` | yes | `processing.transformations` helpers; manual post-filter from `postings/tech/` to an absolute `cv-automation` path. |
| `schedule/emails.py` | no (Git-ignored) | Imports `legal_collect`/`tech_collect` and `io.outputs.send_email`; manual mail sender, not a collection entry. |
| `script.py` | yes | `scrapers.sites.KarriereAT().gather_data()` directly, then writes `data/save/postings_<YYYY-MM-DD>.json`. Experimental; its own `#TODO - fix (i.e. update)` is still open. |
| `schedule/scrape_universal.py` | no (Git-ignored) | Nothing: skeleton whose `main()` body is a docstring. |
| `schedule/derive_profile_from_universal.py` | no (Git-ignored) | Nothing: skeleton whose `main()` body is a docstring. |
| `schedule/universal_pipeline.py` | no (Git-ignored) | Nothing: empty file (0 bytes). |
| `schedule/universal_filter.py` | no (Git-ignored) | Nothing: empty file (0 bytes). |
| `schedule/regexes.py` | yes | No entry point; constant table imported by the legacy scrapers. |

`schedule/` is Git-ignored except `regexes.py`, `tech_collect.py` and
`tech_filter.py` (`.gitignore`). The other scripts in the table exist only in
this working tree; they are not committed and must not be.

### Pipelines and their callers

| Module | Public function | Callers |
| --- | --- | --- |
| `pipelines/cli.py` | `parse_collection_args` | The four `*_collect.py` scripts; `tests/test_collection_cli.py`. |
| `pipelines/collecting.py` | `get_postings` | `schedule/tech_collect.py`, `legal_collect.py`, `tn_collect.py`; `pipelines/pipeline.py::store_step` (line 27); `tests/test_incremental_collection.py` (lines 542, 580). |
| `pipelines/collecting.py` | `scrape_sites`, `validate_postings_quality` | `pipelines/scrape_universal.py`; `scrape_sites` also from `pipeline.py::scrape_step` and the tests. |
| `pipelines/dani.py` | `collect_dani_postings` | `schedule/dani_collect.py`. |
| `pipelines/scrape_universal.py` | `run_universal_scrape_flow` | `pipelines/dani.py`; `tests/test_raw_collection.py`. |
| `pipelines/store_universal.py` | `load_postings`, `store_universal_postings`, `save_incomplete_run`, `merge_observations` | `pipelines/scrape_universal.py`, `pipelines/dani.py`, `processing/derive_profile_postings.py`. |
| `pipelines/pipeline.py` | `run_pipeline` | No caller. The experimental staged wrapper is dead code today. |

### Importers of `scrapers.sites`

`rg --no-ignore -n "scrapers\.sites|scrapers import sites" src tests schedule script.py`

Use `--no-ignore`: ripgrep skips the Git-ignored `schedule/` scripts otherwise,
which hides the `emails.py` importer and the `legal`, `tn` and `dani` callers
below.

| File:line | Symbol |
| --- | --- |
| `src/jobscraping/scrapers/__init__.py:3` | re-exports `BaseScraper`, `KarriereAT`, `Raiffeisen` from `.sites` |
| `src/jobscraping/pipelines/collecting.py:21` | `from jobscraping.scrapers import sites`; used as `sites.KarriereAT`/`sites.Raiffeisen` (line 26) and `sites.BaseScraper` (line 130) |
| `src/jobscraping/processing/postings_utils.py:468` | lazy `BaseScraper` import inside `enrich_postings` |
| `script.py:6` | `from jobscraping.scrapers import sites`; `sites.KarriereAT` at line 9 |
| `schedule/emails.py:19` | `from jobscraping.scrapers import sites`, inside `if __name__ == "__main__"` |
| `tests/test_collection_cli.py:9` | `BUSINESS_DAY_SHIFT`, `BaseScraper`, `KarriereAT`, `Raiffeisen`; line 80 patches `jobscraping.scrapers.sites.time.time` |
| `tests/test_incremental_collection.py:11` | `KarriereAT` |
| `tests/test_raw_collection.py:11` | `KarriereAT`, `Raiffeisen` |

Eight files, nine import/patch lines. The two code importers that keep the
module alive at runtime are `pipelines/collecting.py` and
`processing/postings_utils.py`; `scrapers/__init__.py` is the facade.

### Importers of `collecting.get_postings`

`rg --no-ignore -n "get_postings" src tests schedule`

| File:line | Symbol |
| --- | --- |
| `src/jobscraping/pipelines/collecting.py:179` | definition |
| `src/jobscraping/pipelines/pipeline.py:27` | `collecting.get_postings(**kwargs)` inside `store_step` |
| `schedule/tech_collect.py:14` | import; call at line 41 |
| `schedule/legal_collect.py:7` | import; call at line 452 |
| `schedule/tn_collect.py:12` | import; call at line 314 |
| `tests/test_incremental_collection.py:542`, `:580` | direct calls on the `collecting` module |

Not importers, although `rg` matches them: `schedule/emails.py:2` is a
commented-out import; `schedule/dani_collect.py:10` imports
`collect_dani_postings as get_postings` from `pipelines.dani` (a different
function); `tests/test_collection_cli.py:64` and
`tests/test_incremental_collection.py:228` patch each schedule module's own
`get_postings` alias; `tests/test_incremental_collection.py:513` is a test
name.

### Saved-data layout

All of it is under `data/save/` (`data/*` is Git-ignored; a few old data files
are committed anyway).

Profile folders, `data/save/postings/<profile>/` for `tech`, `legal`, `tn`,
`dani`:

| File | Writer | Present today |
| --- | --- | --- |
| `current_postings.json` | derivation / `get_postings` | all four |
| `postings_history.json` | derivation / `get_postings` | all four |
| `newly_added_postings.json` | derivation / `get_postings` | all four |
| `newly_added_history.md` | `io.outputs.log_to_markdown` | all four |
| `migration_baseline_<YYYY-MM-DD>.json` | derivation, once, before the first migration run | `dani/` only |
| `postings_<timestamp>.json` | `save_data` when `efficient_storing=False` | none today |

Universal, `data/save/postings/universal/`:

| Path | Writer | Present today |
| --- | --- | --- |
| `postings_history.json` | `store_universal_postings` (historical root run) | yes |
| `positive_postings_history.json` | No producer in `src`; unexplained local file | yes |
| `current_postings.json`, `newly_added_postings.json`, `collection_scope.json` | `store_universal_postings`, only when the root path is passed | no |
| `collections/dani/current_postings.json`, `postings_history.json`, `newly_added_postings.json`, `collection_scope.json` | `run_universal_scrape_flow` through `pipelines.dani` | yes |
| `collections/dani/incomplete_run_<timestamp>.json` | `save_incomplete_run` | yes (three files) |

Other outputs: `data/save/excels/excel_<profile>/postings_<date>.xlsx` (also
`legal_jobs_<date>.xlsx` in the legal folder) and
`data/save/companies/karriere.at_companies_*.json`.

Legacy names still on disk, matching
[../design/artifacts.md](../design/artifacts.md):

- `data/save/postings/tech/current_postings_.json`,
  `newly_added_postings_.json`, `postings_2025-08-06-00-32-31.json`: the
  `*_.json` variants. They are tracked in Git and deleted in the current
  working tree; no current writer produces the trailing-underscore form.
- `data/save/postings/legacy/`, `legacy/legal/`, `legacy/temp/`,
  `postings/asd/`, `data/offline/dani-language-2026-11-03/` and
  `data/_merge_backups/`: older dumps (`*_1.json`, `*_2.json`,
  `postings_history_old.json`, `results.csv`, dated `<source>_<timestamp>.json`)
  kept for reference. `design/artifacts.md` also lists the
  `postings_<timestamp>.json` debug dump; the rule holds, no such file exists
  now.

The universal root is the expected layout, not a produced one: the code writes
current/history/newly-added/scope to whatever `path` it is given, and the live
Dani run passes `collections/dani` (Q28).

### Absolute paths

The original baseline was captured before B03, when
`rg "[A-Za-z]:[\\/]|/home/|/Users/" src tests` matched one real path:

| File:line | Value | Source |
| --- | --- | --- |
| `src/jobscraping/config/configs.py:22` (before B03) | `REPO_ROOT_PATH = "C:/GitHubRepo/REPOS/AWS-job-posting-analysis"` | Hand-written machine path. `SAVING_PATH`, `POSTINGS_PATH`, `EXCELS_PATH`, `COMPANIES_PATH` and every schedule path derived from it. |

B03 replaced it: at HEAD, `configs.py:23` derives the root as
`REPO_ROOT_PATH = str(Path(__file__).resolve().parents[3])`, and the pattern
finds zero real paths in `src tests`.

The same pattern also matches URLs (`https://…`), the `\n` in f-strings, and
`r'\b…'` regexes in `src` and `tests`; those are false positives, not paths. No
`/home/` or `/Users/` match exists.

Outside the `src`/`tests` scope, one tracked code path is also absolute:

| File:line | Value |
| --- | --- |
| `schedule/tech_filter.py:16` | `OUTPUT = "C:/GitHubRepo/REPOS/cv-automation/data/raw/postings/tech_filter/"` |

`conf/base/` and `conf/local/` are empty directories; there are no catalog or
parameter files with paths yet.

### Test command

From the repository root:

```powershell
uv run python -m unittest discover -s tests
```

On 2026-11-23, from a clean `uv run` with no manual `PYTHONPATH`, this reported
`Ran 55 tests in 0.334s` / `OK`. That command and that count are the baseline
(B02). PowerShell may report exit code 1 because unittest writes progress to
stderr; read the `OK` line. Per module: `test_collection_cli.py` 8,
`test_incremental_collection.py` 17, `test_raw_collection.py` 11,
`test_dani_profile.py` 14, `test_language_requirements.py` 5.

No test needs the network or a live browser, so the default gate is the whole
suite and excludes nothing; no skip markers are needed. The HTTP helpers are
exercised with a patched `requests.Session` and stubbed
`requests_responses[_with_cookies]`; URLs such as
`https://example.test/jobs` and `https://www.karriere.at/jobs/1` are data or
arguments to those stubs and are never fetched. `selenium` is imported lazily in
`src` only, and no test constructs a driver.

The suite imports files outside Git (the Git-ignored `schedule` modules and the
untracked `pipelines.dani`), so it runs in this working tree but not in a fresh
clone; [Live entry points](#live-entry-points) and the note below the behaviour
table record why. That dependency is unchanged by B02.

The tests that protect each behaviour:

| Module | Behaviour |
| --- | --- |
| `tests/test_collection_cli.py` | CLI parsing and date/business-day forwarding in the four collect scripts |
| `tests/test_incremental_collection.py` | cookie/retry HTTP helpers, cache modes, per-profile cache policy, merge/unify, quality gate before overwrite |
| `tests/test_raw_collection.py` | raw acquisition quality, Karriere 410 pagination, fact reuse, incomplete-run artifacts, Raiffeisen raw mode |
| `tests/test_dani_profile.py` (untracked) | Dani derivation: scores, priority families, exclusions, delta threshold, quality gate |
| `tests/test_language_requirements.py` (untracked) | `LanguageEvidence`, language estimation and Dani language policy |

Discovery imports `schedule.dani_collect` (and through it
`pipelines.dani`), which are Git-ignored/untracked. The command therefore only
runs in this working tree; a fresh clone fails at import until those files are
tracked or the tests stop importing them. B02 records that as the baseline's
known working-tree dependency; see [Test command](#test-command).

### Archive-only and inert scripts

- **Archive-only:** `schedule/hardverapro_collect.py`. It imports
  `jobscraping.scrapers.websites.hardverapro`, which is absent from the tree
  (only a stale `hardverapro.cpython-313.pyc` remains, and
  `scrapers/websites/archive/` is empty). `data/save/postings/hardverapro/`
  does not exist. It is not a migration gate (Q17).
- **Live but untracked:** `dani_collect.py`, `legal_collect.py`,
  `tn_collect.py` and `emails.py`. `tech_filter.py` is tracked and live. None of
  the untracked scripts may be committed as part of this ticket.
- **Inert placeholders, not gates:** `scrape_universal.py` and
  `derive_profile_from_universal.py` (skeletons), `universal_pipeline.py` and
  `universal_filter.py` (empty).

### Corrections to the 2026-11-16 notes

- `scrapers/sites.py` is 1046 lines and `scrapers/basescraper.py` is 458 lines,
  not 974 and 417 as [../README.md](../README.md) still says. The structure is
  unchanged: `BaseScraper`, `KarriereAT`, `Raiffeisen` in `sites.py`, a second
  `BaseScraper` in `basescraper.py`, and close site variants in
  `scrapers/websites/karriere_at.py` and `raiffeisen.py`.
- `pyproject.toml` requires Python `>=3.13.18`, not `>=3.13.17`.
- The universal root does not hold current/newly-added/scope today; only
  `postings_history.json` and `positive_postings_history.json` are there. The
  live current/newly-added/scope files are under `collections/dani/`. The
  [artifacts table](../design/artifacts.md) describes the code contract, not
  the current root contents.
- The 54-test note is stale; the working tree reports 55 (B02's
  `Ran 55 tests`). The untracked `tests/test_dani_profile.py` alone contributes
  14 of those, so it does not explain the one-test difference by itself.

## Gates

Each gate must pass before the next consumer switches.

1. **Import gate.** One scraper implementation; split modules exported; no
   stale `scrapers.sites` import. Legacy pipeline still works. (Hardverapro is
   archive-only and not part of this gate.)
2. **Data gate.** Pure merge/compare/enrich with fixtures; reruns idempotent;
   profile policy fields absent from universal records, profile-neutral
   annotations present.
3. **Universal gate.** Collection writes chunks, resume works, a failed quality
   check leaves the previous snapshot intact.
4. **Profile gate.** Dani derives from universal facts with unchanged selected
   output. Other profiles remain on the legacy path.
5. **Output gate.** Outputs regenerate from saved artifacts.
6. **Kedro gate.** `kedro run` reproduces the script path for collection and one
   derivation, with parameters only from `conf/`.
7. **Cleanup gate.** No consumer imports a superseded module; archive it.
8. **Portability gate.** No committed absolute path; the project runs from a
   fresh clone with relative paths.

## Compatibility rules

- A compatibility adapter must name its caller. No caller, no adapter.
- Profile-processing methods on `BaseScraper` are temporary adapters; they are
  removed when derivation owns filtering and scoring.
- Do not keep two entry points that do the same thing after the Kedro gate.
- `Hardverapro` is archive-only; its broken import may stay until cleanup and is
  not a migration gate (Q17).

## Verified stale claims

These were checked on 2026-11-16 and must not be copied forward:

- The old migration inventory says `scrapers/sites.py` was deleted; it is the
  active implementation here.
- `scrapers/websites/hardverapro.py` is imported by
  `schedule/hardverapro_collect.py` but does not exist. The script is
  archive-only; it may stay broken until cleanup.
- `processing/candidate_filtering.py`, `selection_filtering.py` and `scoring.py`
  are empty, not implemented.
- `docs/adr/0001-collection-and-profile-ownership.md` is the ownership source;
  the process map's step ordering is a proposal, not an approval.

## Cutover sequence

1. Dani: legacy profile script → separated collection + derivation (partly
   done), then Kedro flow.
2. Tech: move constants unchanged, verify parity, switch.
3. Legal: same, after tech.
4. Tn: same, after legal.
5. Retire `collecting.get_postings`, the experimental `pipeline.py`, empty
   skeletons and unused schedule scripts.
6. Update runtime documentation, glossary and ADR set.

## Completion check

- One documented way to run collection, one per profile derivation, one for
  outputs.
- No module is retained only for backwards compatibility.
- Every removed file has a replacement that was verified first.
- The baseline note in this document matches the tree at the end of migration.

## Still open

- Q16, the compatibility layer for `scrapers.sites` and
  `collecting.get_postings`. Decide when the first caller moves.
- Which consumers must keep working during the migration (scheduled tasks,
  cv-automation, manual scripts).
- Whether tech migrates before Kedro or becomes the first Kedro pipeline.

Saved-data compatibility is not required (Q27); only code compatibility has to
be managed.

## Design references

- [Decisions](../design/open-questions.md)
- [Process map](../process_map.md)
