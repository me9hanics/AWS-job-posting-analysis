# B05 — Fixture pages and parser parity

Status: done · Milestone: M1 Safe baseline · Phase 0 · Size: M

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

## Implementation notes

Fixtures were captured 2026-11-23 from the live endpoints (provenance in the
`tests/test_scraper_fixtures.py` docstring) and trimmed by hand: cookies, CSRF
and session tokens, scripts, tracking and personal fields removed; only fields
the parser reads plus a little surrounding shape remain.

`KarriereAT.gather_data` still owns both parse steps, so the fixtures pin them
through the live entry point:

- **Listing** — In: one `data.jobsSearchList.activeItems.items` payload. Does:
  iterate `jobsItem` entries and read id, title, company, locations, salary,
  isActive, isHomeOffice, employmentTypes, link, snippet and date. Out:
  postings keyed `karriere.at<id>`. Next: optional detail fetch.
- **Detail** — In: one `data.jobDetailContent` payload. Does: take
  `jobContent.text` and strip HTML to text. Out: description attached to the
  posting whose prefixed id matches `jobHeader.job.id`. Next: `gather_data`
  processing.

B12/B13 need those as two pure functions — a listing payload into postings and
a detail payload into a description — so the steps can be declared without
HTTP, as sketched in [design/collection-steps.md](../../design/collection-steps.md).
Raiffeisen already exposes separable helpers (`_process_posting_soups`,
`_get_descriptions_from_soups`); Karriere does not. No `src/` change in this
ticket.

`tests/test_scraper_fixtures.py` drives those two Raiffeisen helpers directly
with the fixture soups, without HTTP or a browser. Karriere stays on the
`gather_data` path until B12 splits it.

- **Flow assertion.** The exact request sequence in the Karriere test is
  deliberate: it pins the listing page walk before the detail fetch and is
  checked by a session that raises on any unexpected URL, so a reordering or an
  extra network hop fails loudly. `salary_guessed is None` pins that the detail
  fixture carries no salary text, not a broader salary rule.

Observed, not fixed: Karriere's `date` is the site's localised relative string
("Gestern veröffentlicht"), copied verbatim into the posting.
