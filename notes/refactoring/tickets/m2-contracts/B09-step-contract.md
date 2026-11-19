# B09 — Define the adapter step contract

Status: todo · Milestone: M2 Contracts · Phase 1 · Size: S

- Depends on: B06
- Files: `src/jobscraping/scrapers/steps.py`

## Do

1. Add a small frozen `Step` (`name`, `run`, optional `input_spec`,
   `output_spec`).
2. Add a `SiteAdapter` protocol (`source`, ordered `steps`).
3. Document that a step list may be plain `(name, callable)` pairs; the dataclass
   is a convenience, not a framework.
4. Do not add required/optional flags, a registry base class or a validation
   hierarchy.

## Done when

- The module imports with no runtime use.
- A one-step and a two-step adapter can both be described by the types.
