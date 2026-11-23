# Breakdown

Status: decisions recorded 2026-11-16. Each document describes one workstream at
a level between [the plan](../plan.md) and [the design](../design/README.md).

A workstream document answers: what is the current state, what is the target,
which changes get us there, what must happen first, and how we know it is done.
It does not contain field-level interfaces or file contents; those live in
`design/`.

| Workstream | Covers | Plan phases | Design references |
| --- | --- | --- | --- |
| [Collection](collection.md) | Scraper mechanics, parsing, site adapters and steps, universal collector, quality gates | 1, 4 | [collection-steps](../design/collection-steps.md), [module-seams](../design/module-seams.md) |
| [Data](data.md) | Universal vault, merge/compare/enrich, backfill, history semantics | 2 | [specs](../design/specs.md), [artifacts](../design/artifacts.md) |
| [Profiles](profiles.md) | Candidate filter, scoring, selection, language policy, per-profile config | 3 | [specs](../design/specs.md), [module-seams](../design/module-seams.md) |
| [Pipelines](pipelines.md) | Stage orchestration, resume, Kedro project, `conf/`, catalog, parameters | 4, 5 | [kedro-project](../design/kedro-project.md), [artifacts](../design/artifacts.md) |
| [Outputs](outputs.md) | Excel, Markdown, email, output orchestration | 3, 6 | [module-seams](../design/module-seams.md) |
| [Migration](migration.md) | Baseline, sequencing, cutover per consumer, compatibility, cleanup | 0, 6 | [decisions](../design/open-questions.md) |

## Rules

- One workstream owns each artifact and each behaviour. If two documents claim
  the same responsibility, the ownership is wrong.
- A change listed here is a plan, not approval. Runtime changes need the
  matching phase's completion check.
- When a workstream's detail outgrows this level, add a design document rather
  than expanding the breakdown.

## Order

The dependency order is stated in [the plan](../plan.md#phases), expanded in
[the process map](../process_map.md), and made executable in
[the backlog](../backlog.md). In short: baseline → data specs and adapter step
list → collapse duplicates → pure data operations → profile policy → stage
artifacts → Kedro → cleanup. Kedro is deliberately late, because nodes should
wrap stable stage functions rather than the current mixed functions.

The site list grows soon; collapsing duplicates before adding sites is what
keeps that growth cheap.
