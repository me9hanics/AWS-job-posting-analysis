# Tickets

Status: operational view of the [backlog](../backlog.md), 2026-11-19. The backlog
stays the source of truth; these files are one ticket per task and exist so each
task can be picked up, tracked and closed on its own.

`B01`–`B46` are the backlog tasks. `B02a` is one task that was missing from the
backlog and was added early, by decision on 2026-11-19; it inserts without
renumbering anything else. `B07a` is a follow-up to the closed B07/B08 specs after
Q29 (2026-11-24) and is placed after B08.

## Layout

```text
tickets/
  README.md              # this file: index, order, status
  m1-safe-baseline/      # B01, B02, B02a, B03, B04, B05
  m2-contracts/          # B06–B10
  m3-one-scraper-per-site/   # B11–B18
  m4-collector/          # B19–B25
  m5-data-layer/         # B26–B31
  m6-profiles/           # B32–B35
  m7-stages/             # B36–B39
  m8-kedro/              # B40–B43
  m9-done/               # B44–B46
```

Every milestone folder also holds one `implementation-flow.md`: the milestone's
own `In → Does → Out → Next` view, organized one section per ticket in
implementation order, each with the mock shapes that ticket introduces. It may
be brief, but it must exist. M1 predates the rule and has none.

Folders follow the backlog milestones, because a milestone is what "done" means
for a reviewable batch; the backlog's phases are mapped to them by the table
below.

## Status

Status values: `todo` / `doing` / `done` / `blocked`. Update a row and the
ticket's status line in the same change.

### M1 — Safe baseline (phase 0)

| ID | Ticket | Depends on | Status |
| --- | --- | --- | --- |
| B01 | [Record the baseline](m1-safe-baseline/B01-record-the-baseline.md) | — | done |
| B02 | [Confirm the test command and baseline result](m1-safe-baseline/B02-confirm-test-command.md) | B01 | done |
| B03 | [Remove the absolute repository root](m1-safe-baseline/B03-remove-absolute-root.md) | B02 | done |
| B04 | [Characterization tests for data rules](m1-safe-baseline/B04-characterization-tests.md) | B02 | done |
| B02a | [Add a real `last_modified_on` field](m1-safe-baseline/B02a-last-modified-on-field.md) | B04 | done |
| B05 | [Fixture pages and parser parity](m1-safe-baseline/B05-fixture-pages.md) | B02, B03 | done |

Execution order inside M1: B01 → B02 → B03 → B04 → B02a → B05. B02a is placed
early on purpose (see its ticket) and needs B04's merge fixtures to prove itself.

Confirmed during M1:

- **B02a** — confirmed 2026-11-23: `last_modified_on` is computed only in the
  merge, appears in `COLUMN_ORDER` right after `date`, and gets no Excel column.

### M2 — Contracts (phase 1)

| ID | Ticket | Depends on | Status |
| --- | --- | --- | --- |
| B06 | [Create the `specs` package](m2-contracts/B06-create-specs-package.md) | B02 | done |
| B07 | [Define the five posting specs](m2-contracts/B07-posting-specs.md) | B06 | done |
| B07a | [Put profile-neutral annotations in the universal spec](m2-contracts/B07a-universal-annotations.md) | B07, B08 | done |
| B08 | [Test the spec contract](m2-contracts/B08-spec-contract-tests.md) | B06, B07 | done |
| B09 | [Define the adapter step contract](m2-contracts/B09-step-contract.md) | B06 | done |
| B10 | [Prove the step contract with a fake adapter](m2-contracts/B10-fake-adapter.md) | B09 | done |

B06–B10 may run in parallel with B03–B05 once B02 is done. The milestone flow is
[implementation-flow.md](m2-contracts/implementation-flow.md).

B07a is a follow-up to B07/B08 rather than a reopened ticket: it adds the
profile-neutral annotations (`language`, `guessed_required_languages`) to
`UNIVERSAL_POSTINGS` after Q29 (2026-11-24). It changes the specs' field list and
one test, no runtime behaviour. Its producers land in B29/B31; B33 consumes them.

### M3 — One scraper per site (phases 2–3)

| ID | Ticket | Depends on | Status |
| --- | --- | --- | --- |
| B11 | [Choose the canonical scraper implementations](m3-one-scraper-per-site/B11-canonical-scrapers.md) | B05 | done |
| B12 | [Move `KarriereAT` to its site module](m3-one-scraper-per-site/B12-move-karriere-at.md) | B11 | done |
| B13 | [Move `Raiffeisen` to its site module](m3-one-scraper-per-site/B13-move-raiffeisen.md) | B12 | done |
| B14 | [Make `BaseScraper` single-source and shrink `sites.py`](m3-one-scraper-per-site/B14-single-base-scraper.md) | B13 | done |
| B15 | [Update every importer](m3-one-scraper-per-site/B15-update-importers.md) | B14 | done |
| B16 | [Extract the HTTP path](m3-one-scraper-per-site/B16-extract-http.md) | B15 | done |
| B17 | [Extract the headless-browser path](m3-one-scraper-per-site/B17-extract-browser.md) | B16 | done |
| B18 | [Extract pagination and retire the facade](m3-one-scraper-per-site/B18-extract-pagination.md) | B17 | done |

### M4 — Collector (phase 4)

| ID | Ticket | Depends on | Status |
| --- | --- | --- | --- |
| B19 | [Give `KarriereAT` declared steps](m4-collector/B19-karriere-steps.md) | B12, B16, B17, B18 | done |
| B20 | [Give `Raiffeisen` declared steps](m4-collector/B20-raiffeisen-steps.md) | B13, B19 | done |
| B21 | [Extract the quality gate](m4-collector/B21-quality-gate.md) | B15 | done |
| B22 | [Create the universal collector](m4-collector/B22-universal-collector.md) | B09, B10, B19, B20, B21 | done |
| B23 | [Add chunk artifacts and the JSON run report](m4-collector/B23-chunks-and-report.md) | B22 | done |
| B24 | [Wire the universal pipeline to the collector](m4-collector/B24-wire-universal-pipeline.md) | B22, B23 | todo |
| B25 | [Collector integration tests](m4-collector/B25-collector-integration-tests.md) | B24 | todo |

### M5 — Data layer (phase 5)

| ID | Ticket | Depends on | Status |
| --- | --- | --- | --- |
| B26 | [Create `data/load.py`](m5-data-layer/B26-data-load.md) | B03 | todo |
| B27 | [Move merge and history rebuild](m5-data-layer/B27-data-merge.md) | B26, B04, B02a | todo |
| B28 | [Make the diff neutral](m5-data-layer/B28-neutral-diff.md) | B27 | todo |
| B29 | [Move generic enrichment and remove the scraper import](m5-data-layer/B29-data-enrich.md) | B27, B28 | todo |
| B30 | [Atomic writes, UTC and `schema_version`](m5-data-layer/B30-atomic-writes.md) | B26 | todo |
| B31 | [Store every posting in universal](m5-data-layer/B31-store-every-posting.md) | B22, B24, B27 | todo |

### M6 — Profiles (phase 6)

| ID | Ticket | Depends on | Status |
| --- | --- | --- | --- |
| B32 | [Add `ProfileConfig`](m6-profiles/B32-profile-config.md) | B07 | todo |
| B33 | [Make derivation generic](m6-profiles/B33-generic-derivation.md) | B27, B28, B32 | todo |
| B34 | [Move profile rules and delete the empty modules](m6-profiles/B34-profile-rules.md) | B33 | todo |
| B35 | [Make profile current selected-only](m6-profiles/B35-selected-only-current.md) | B33, B34 | todo |

### M7 — Stages (phase 7)

| ID | Ticket | Depends on | Status |
| --- | --- | --- | --- |
| B36 | [Extract stage functions](m7-stages/B36-stage-functions.md) | B24, B33 | todo |
| B37 | [Add spec checks at stage boundaries](m7-stages/B37-stage-spec-checks.md) | B36 | todo |
| B38 | [Resume, partial failure and incomplete-run artifact](m7-stages/B38-resume-and-failure.md) | B23, B36 | todo |
| B39 | [Backfill dry run](m7-stages/B39-backfill-dry-run.md) | B30, B31 | todo (optional) |

### M8 — Kedro (phase 8, user-owned)

| ID | Ticket | Depends on | Status |
| --- | --- | --- | --- |
| B40 | [Add the Kedro skeleton](m8-kedro/B40-kedro-skeleton.md) | B36 | todo |
| B41 | [Add `conf/` parameters and a relative catalog](m8-kedro/B41-conf-and-catalog.md) | B40, B32 | todo |
| B42 | [Build the collection pipeline](m8-kedro/B42-collection-pipeline.md) | B41, B24 | todo |
| B43 | [Build derivation and outputs; parity check](m8-kedro/B43-derivation-pipeline.md) | B42, B36 | todo |

### M9 — Done (phase 9)

| ID | Ticket | Depends on | Status |
| --- | --- | --- | --- |
| B44 | [Remove compatibility code and stale modules](m9-done/B44-remove-compatibility.md) | B43 | todo |
| B45 | [Update documentation and ADRs](m9-done/B45-update-docs.md) | B44 | todo |
| B45b | [Sphinx documentation in `docs/`](m9-done/B45b-sphinx-docs.md) | B45 | todo |
| B46 | [Final gates](m9-done/B46-final-gates.md) | B44, B45b | todo |

## Ticket implementation notes

Tickets do not get companion prototype files or placeholders. The one companion
file a milestone carries is its `implementation-flow.md` (see
[Layout](#layout)). That file is scoped to the milestone but divided per ticket:
it lists the tickets in implementation order and shows, for each, the mock
shapes the ticket introduces and its `In → Does → Out → Next` chain. A ticket
that builds one continuous segment gets one chain; a ticket with unrelated parts
gets one chain per part. This is where "what will exist, and where it fits" is
written down.

A ticket's own `## Implementation notes` section stays scoped to that ticket:
state what changes and, only where it clarifies the work, use
`In → Does → Out → Next` for a local handoff the milestone file does not
already cover. Link to the milestone's `implementation-flow.md` and to the
design sketch instead of repeating them.

Mock signatures in a ticket are illustrative only. The design documents remain
the source for cross-block interfaces and data flow; the milestone flow file is
the ordered, per-ticket view of that flow; the ticket remains the source for the
scoped change and its completion checks.

## Working agreement

Repeated in every ticket so each ticket can be read alone.

- One ticket per reviewable change. Put the `Bxx` ID in the commit message.
- Tick a ticket only when its **Done when** line is true, then update the status
  row here in the same commit.
- If a ticket outgrows one change, split it into `Bxxa`/`Bxxb` in the backlog and
  here rather than hiding the size.
- Respect **Depends on**. Leave the suite green after every ticket.
- Check new code with `ruff` and `ty` (see
  [Linting and typing](#linting-and-typing)). Findings in old code the ticket
  only moves or leaves untouched are reported, not swept into the ticket.
- If `ruff` reports too many arguments on code the ticket writes, stop and ask
  the user with two or three concrete variants (group into a config or request
  object, keyword-only with defaults, split the function, an accepted `noqa`).
  Do not choose silently and do not add `noqa` just to make the check pass.
- If implementation shows a design decision is wrong, fix the design document
  first, then the backlog, then the ticket.
- The tree contains the user's in-progress work. Never revert, clean, restore or
  commit unrelated changes.

## Verification commands

Run from the repository root:

```powershell
uv run python -m unittest discover -s tests
```

PowerShell can report exit code 1 because unittest writes to stderr even when
tests pass; read the `OK`/failure output. At the end of M3 the runner reports 114
tests with this working tree — 84 tracked test methods plus 30 from the untracked
WIP test modules (`test_dani_profile.py`, `test_language_requirements.py`,
`test_raw_collection.py`). Quote 114 only as "reported", not as the tracked
count.

A ticket that claims "no absolute path" is verified with:

```powershell
rg "[A-Za-z]:[\\/]|/home/|/Users/" src tests
```

A ticket that claims "no duplicate scraper" is verified with:

```powershell
rg "class BaseScraper|class KarriereAT|class Raiffeisen" src
```

### Linting and typing

Ruff and ty join the gates from B21 on. Run them on the files the ticket
touched, or on the tree:

```powershell
uvx ruff check src tests
uvx ty check src
```

`uvx` is used because neither tool is a project dependency yet; B46 may add them
as a dev group, after which `uv run ruff` and `uv run ty` replace `uvx`.

The rule is about **new code**. A ticket leaves the code it writes or rewrites
clean. Findings in code the ticket only moves, imports or leaves untouched are
out of scope: list them (file, rule, line) in the ticket notes and keep them, or
fix one only when the fix is a trivial local edit the move itself created (an
unused import, a renamed symbol). Never reformat an old file to quiet a checker.
B46 runs both tools over the whole tree.

"Too many arguments" (`PLR0913`) is the expected exception. New functions such
as the collector entry point or a step may legitimately grow parameters; when
that finding appears, ask the user before changing the shape, and offer the
variants above. Silent `# noqa` on new code is not a resolution.

## Still open

- **Q16** — the compatibility layer. B11 decided the `scrapers.sites` half (no
  layer beyond the move). M4 follows the stated default for
  `collecting.get_postings`: `gather_data` wrappers and `scrape_sites` live
  while their named callers exist and are removed in B44. See
  [m4-collector/implementation-flow.md](m4-collector/implementation-flow.md#decisions-this-plan-fixes).
- **Q28** — the universal history is expected but not guaranteed. Derived from
  the user's clarification on 2026-11-22; it constrains B32, B33, B36 and the
  derivation tests, not the folder layout. See
  [design/open-questions.md](../design/open-questions.md#universal-history-is-not-guaranteed).
- **Q31** — the cache logic surface. M4 ships run-level cache inputs; a supplied
  callable and per-site caching are possible later and are not built now. See
  [design/open-questions.md](../design/open-questions.md#q31-cache-logic-surface).
- **Q32** — universal history-only mode. `current`, `newly-added` and the scope
  file stay views over history, so dropping them later is a write-path change.
  It constrains B27, B28, B30 and B31. See
  [design/open-questions.md](../design/open-questions.md#q32-universal-history-only-mode).
