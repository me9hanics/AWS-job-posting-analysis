# B02 — Confirm a clean test command and baseline result

Status: done · Milestone: M1 Safe baseline · Phase 0 · Size: S

- Depends on: B01
- Files: [backlog.md](../../backlog.md), [breakdown/migration.md](../../breakdown/migration.md)

## Do

1. Run `uv run python -m unittest discover -s tests`.
2. Record the number of tests and the command in the baseline.
3. If a test needs the network, mark it and exclude it from the default gate.

## Done when

- The command passes from a clean `uv run` without manual `PYTHONPATH`.
- The baseline names the command and the pass count.

## Notes

At review time, 54 tests passed with this command. B02 confirmed 55 on
2026-11-23 (`Ran 55 tests in 0.334s` / `OK`); PowerShell may report exit
code 1 because unittest writes to stderr; judge by the `OK`/failure output.
