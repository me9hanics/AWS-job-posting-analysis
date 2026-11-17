# Migration workstream

Status: decided direction 2026-11-16. Baseline is partly documented; cutover
per profile is not scheduled.

Owns the order in which parts move, what must be proven before a consumer
switches, which compatibility code may exist temporarily, and what gets removed.

This document condenses [process_map.md](../process_map.md); the process map
remains the detailed reference. Where they disagree, the process map's open
questions win until a decision is recorded here.

## Baseline to capture (Phase 0)

- Live entry points and what calls them: `schedule/tech_collect.py`,
  `legal_collect.py`, `dani_collect.py`, `tn_collect.py`,
  `hardverapro_collect.py`, `derive_profile_from_universal.py`,
  `scrape_universal.py`, `universal_pipeline.py`, `universal_filter.py`,
  `script.py`.
- Imports of `scrapers.sites` and of `collecting.get_postings`.
- Saved-data layout per profile and for the universal vault, including legacy
  filenames and the `*_.json` variants.
- The current test command and which tests protect which behaviour.
- Which values are machine-specific and must not be committed. The known case
  is the absolute `REPO_ROOT_PATH` in `config/configs.py`; it must become a root
  derived from `__file__`, not a `conf/local/` value.
- Every other absolute path in code, config or catalog files.

## Gates

Each gate must pass before the next consumer switches.

1. **Import gate.** One scraper implementation; split modules exported; no
   stale `scrapers.sites` import. Legacy pipeline still works. (Hardverapro is
   archive-only and not part of this gate.)
2. **Data gate.** Pure merge/compare/enrich with fixtures; reruns idempotent;
   profile fields absent from universal records.
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
