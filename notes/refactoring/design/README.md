# Design

Status: decided 2026-11-16 except Q16. Design documents hold concrete
interfaces, module maps and layout; the workstreams in
[breakdown/](../breakdown/README.md) hold the work.

| Document | Answers |
| --- | --- |
| [Module seams](module-seams.md) | Which parts become separate modules, which stay together, and which dependency directions are allowed. |
| [Specs and dataclasses](specs.md) | Data specs per step, which dataclasses remain, and which candidates were dropped. |
| [Collection steps](collection-steps.md) | Adapter-defined steps, skippable steps, partial results and the universal collector. |
| [Kedro project](kedro-project.md) | Package layout, `conf/`, catalog, parameters, node/flow options, migration path. |
| [Artifacts](artifacts.md) | Artifact paths, naming, merge semantics, resume and failure behaviour. |
| [Decisions](open-questions.md) | The decision log and the one remaining open question. |

## Status labels

- `agreed` / `decided` — decided; changing it needs a new decision in this
  folder.
- `proposed` — the current default for discussion. Implementation may start on
  a proposal only when the workstream's completion check is accepted.
- `open` — no default; the question is listed in
  [open-questions.md](open-questions.md).

## Rules

- A design document describes one seam. If it needs another seam's internals to
  explain itself, the boundary is wrong.
- Code sketches are illustrations of shape, not final signatures. Keep them
  short enough that changing them is cheap.
- When a question is decided, update the document and the corresponding row in
  [open-questions.md](open-questions.md) in the same change.
- Cross-references use relative links so the folder can move as a unit.
