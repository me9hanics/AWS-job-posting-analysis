# B31 — Store every posting in universal

Status: todo · Milestone: M5 Data layer · Phase 5 · Size: M

- Depends on: B22, B24, B27
- Files: `scrapers/basescraper.py`, `pipelines/scrape_universal.py`,
  `data/merge.py`, tests

## Do

1. Make the universal path stop running role/manager/relevance filtering;
   profiles own it.
2. Keep the legacy profile path behaviour until its cutover; do not change
   `get_postings` in this ticket.
3. Keep only factual normalization and quality gates on the universal path.
4. Ensure a posting that a profile would reject still appears in universal.
5. Store the profile-neutral annotations from B29 (`language`,
   `guessed_required_languages`) next to `matched_titlewords` (Q29).

## Implementation notes

"Profile field" now means profile *policy*. The universal record keeps
`language`, `guessed_required_languages` and `matched_titlewords`; it drops
`points`, `keywords`, `role_families`, `language_adjustment`,
`language_excluded` and `profile_excluded`. See
[design/specs.md](../../design/specs.md#profile-neutral-annotations).

The store happens after enrichment, so merge must not overwrite the annotations
with stale values: treat them as derived fields replaced by the latest
enrichment, not merged as lists.

## Done when

- A fixture with a manager/irrelevant title is stored in universal.
- The same posting can be rejected by a profile.
- The legacy profile tests still pass.
- Universal records carry the three annotations and no policy field.
- The stored record passes `UNIVERSAL_POSTINGS.check`.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)). Every stored fact lands
  in history; `current` and `newly-added` stay views over it (Q32).
