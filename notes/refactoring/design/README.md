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

## Implementation-flow sketches

Add an implementation-flow sketch to the relevant design document when a
design decision needs to show how data moves through several logical blocks.
The cross-block sketch lives in the design document; each milestone's own view
of the flow it implements lives in
`tickets/<milestone>/implementation-flow.md` and must exist even when brief.
There are no separate per-ticket sketch files and no placeholders; per-ticket
blocks live inside the milestone file. The agent planning or starting a
milestone writes both.

The sketch follows the data in execution order: pipeline context before the
change, then each logical block, then the downstream artifact or stage. Each
block states:

- **In:** the data, config, or artifact it receives and its producer;
- **Does:** the short transformation or decision it makes;
- **Out:** the named result and its shape;
- **Next:** the named consumer of that result and why it consumes it.

Where a block contains smaller relevant blocks, list them in their execution
order with the same `In → Does → Out → Next` chain. Small mock signatures or
dataclasses may show a boundary, but their names and types must connect the
preceding block's output to the next block's input. They are design sketches,
not implementation or a second source of truth.

### Milestone sketches: organize by ticket

The milestone file is the bridge between the spec and the tickets, so it is
organized the way the work is: one section per ticket, in implementation order.
Each section gives that ticket its own chain and shows the mock shapes the
ticket introduces (dataclasses, signatures, constants, report fields), so a
reader can see what will exist and where it fits before any code is written.

- A ticket that builds one continuous segment of the pipeline gets one chain:
  input, its parts in execution order, output.
- A ticket whose parts are not continuous (two unrelated classes, a class and
  its tests, two independent modules) gets one chain per part.
- Short mock code is the point, not decoration: show the shape the next ticket
  will consume. Keep it to the boundary, and make its names and types match the
  neighbouring blocks.
- End with one short end-to-end chain across the milestone, if the tickets
  together form a flow. Do not repeat every detail there.

A ticket's own `## Implementation notes` stays scoped to that ticket and links
to the milestone file instead of restating it.
