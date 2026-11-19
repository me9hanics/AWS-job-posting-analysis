# B05 — Fixture pages and parser parity

Status: todo · Milestone: M1 Safe baseline · Phase 0 · Size: M

- Depends on: B02, B03
- Files: `tests/fixtures/karriere/`, `tests/fixtures/raiffeisen/`, `tests/`

## Do

1. Capture one listing payload and one detail payload per site as small
   fixtures. Strip cookies, tokens and personal data.
2. Test the extraction/parsing functions that do not require a live browser.
3. If a parser is trapped inside a live `gather_data` call, record the seam
   needed for B12/B13 instead of forcing a network test.

## Done when

- At least one listing and one detail fixture per site parse to expected facts
  without network access.
- The fixtures are small enough to review.
