# B20 — Give `Raiffeisen` declared steps

Status: todo · Milestone: M4 Collector · Phase 4 · Size: M

- Depends on: B13, B19
- Files: `scrapers/websites/raiffeisen.py`

## Do

1. Same split as B19, using Raiffeisen's actual flow.
2. Keep a single-step path if that is what the site actually does.
3. Keep the legacy wrapper until B24.

## Done when

- The adapter exposes its steps in order.
- Fixture parity holds.
- The two site modules do not share a hidden "main" step.
