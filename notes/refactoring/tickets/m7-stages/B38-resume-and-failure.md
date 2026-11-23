# B38 — Resume, partial failure and incomplete-run artifact

Status: todo · Milestone: M7 Stages · Phase 7 · Size: M

- Depends on: B23, B36
- Files: `acquisition/chunks.py`, stage modules, `io/files_io.py`

## Do

1. Reuse valid chunks for the same scope digest.
2. Write one `incomplete_run_<timestamp>.json` on a rejected quality gate.
3. Leave the previous current/history untouched on failure.

## Done when

- Interrupt and resume reproduce the same vault.
- A failed gate leaves the prior snapshot intact and writes one artifact.
- A skipped step remains visible as a missing chunk.
