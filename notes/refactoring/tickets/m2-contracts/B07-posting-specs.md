# B07 — Define the five posting specs

Status: done · Milestone: M2 Contracts · Phase 1 · Size: S

- Depends on: B06
- Files: `src/jobscraping/specs/postings.py`

## Do

1. Add `DISCOVERED_POSTINGS`, `COLLECTED_POSTINGS`, `UNIVERSAL_POSTINGS`,
   `SCORED_POSTINGS`, `SELECTED_POSTINGS`.
2. Use the field names that exist in `RAW_POSTING_FIELDS`, `store_universal` and
   `derive_profile_postings`; do not invent a new vocabulary.
3. Keep required fields minimal (identity and URL); move completeness to the
   quality gate.
4. Keep profile fields out of `UNIVERSAL_POSTINGS`.
5. Include `last_modified_on` from B02a in `UNIVERSAL_POSTINGS`.

## Done when

- All five import.
- The field sets match [design/specs.md](../../design/specs.md#specs-per-step).
- No profile-only key appears in `UNIVERSAL_POSTINGS`.
