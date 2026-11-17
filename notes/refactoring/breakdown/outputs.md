# Outputs workstream

Status: decided direction 2026-11-16. Rendering is partly separated;
orchestration is not.

Owns turning selected profile postings into deliverables: Excel, Markdown log,
optional email, company files. It does not own scoring or selection.

## Current state

- `io/outputs.py` (194 lines) mixes DataFrame preparation, Excel orchestration,
  Markdown logging and email sending. `generate_outputs` prepares data and calls
  the Excel renderer.
- `io/outputs_excel.py` (109 lines) holds `remove_bad_chars` and
  `create_excel_report` — a working renderer plus cleaning helpers.
- `io/generate_profile_outputs.py` is an explicit placeholder with four empty
  functions. It documents the intended orchestration but is not wired.
- `config/constants.py` holds `COLUMN_ORDER` and `EXCEL_COLUMNS`; profile scripts
  pass their own column selections.
- `schedule/*_collect.py` calls output functions directly, so output policy is
  spread across scripts.
- Output paths are absolute through `config/configs.py` (`REPO_ROOT_PATH`,
  `EXCELS_PATH`, `COMPANIES_PATH`). They become relative to a root derived from
  `__file__`.

## Target

Two layers:

1. **Renderers** — pure-ish functions: given rows and options, return a file
   path or bytes. No knowledge of profiles, history or pipelines.
2. **Output orchestration** — read selected artifacts, choose which formats the
   profile wants, call renderers, return produced paths.

Output selection becomes part of the profile policy (for example: Excel always,
Markdown log when newly added is non-empty, email optional), not a script-level
convention.

## Changes

1. Move DataFrame preparation out of `outputs.generate_outputs` into an
   Excel-named helper in `outputs_excel.py`; leave `generate_outputs` as the
   compatibility caller until the pipeline switch.
2. Implement `generate_profile_outputs` as orchestration over selected current
   and newly-added artifacts.
3. Make column layout and filename conventions explicit parameters, not hidden
   constants, then move the tunable ones to profile configuration or `conf/`.
4. Keep `log_to_markdown` and `send_email` independent of Excel and of each
   other.
5. Make outputs regenerable from saved artifacts with no collection run.
6. Company files are exports or BI views derived from records, not a pipeline
   dataset (Q18). Produce them on demand, not as a stage artifact.

## Dependencies

- Profiles workstream: which outputs a profile requests.
- Data workstream: selected and newly-added artifacts are the inputs.
- Kedro: Excel is a dataset; Markdown and email are side effects for now (Q10).

## Completion check

- Regenerating outputs from saved artifacts produces the same Excel content as
  the current script for one fixture profile.
- Renderers import no profile module and no pipeline module.
- A profile with no newly-added postings produces no empty Markdown section or
  fails deliberately; behaviour is explicit.
- No output module reads a configuration value that belongs to a profile policy.
- No output path is absolute; regenerating outputs from a fresh clone works.

## Decided points

- Excel is a Kedro dataset; Markdown and email are side effects for now (Q10,
  preliminary).
- Output options are `conf/` profile parameters (Q6).
- Company files are exports, not datasets (Q18).

Still implementation details: whether email remains required, and the exact
dataset class for Excel. The only open design question is Q16. See
[open-questions.md](../design/open-questions.md#still-open).

## Design references

- [Module seams](../design/module-seams.md)
- [Kedro project](../design/kedro-project.md)
- [Decisions](../design/open-questions.md)
