# B27a — Non-empty observations win

Status: done · Milestone: M5 Data layer · Phase 5 · Size: M

- Depends on: B27
- Files: `src/jobscraping/data/merge.py`, `tests/test_data_rules.py`,
  `tests/fixtures/merge_expected.json`, `tests/fixtures/merge_current.json`

## Do

1. Replace the blanket `{**old, **posting}` update with the grouped rule from
   [artifacts.md](../../design/artifacts.md#merge-and-diff-rules). A field is
   handled by exactly one group:
   - **observed facts** — a non-empty observation replaces; absent, `""`,
     `None`, `[]` or `{}` leaves the stored value (`False` and `0` are values);
   - **derived fields** (`language`, `guessed_required_languages`,
     `salary_guessed`, `salary_monthly_guessed`) — a present key is
     authoritative and replaces even when its recomputed value is empty or
     `None`;
   - **always fresh** — `collected_on`, `date`, `isActive`, `url`;
   - **merge-owned** — the date range fields and `last_modified_on`;
   - **provenance** — `matched_titlewords` unions in order.
2. Make `_material_changed` agree: an absent or empty `title`/`description` is
   not a material change, so `last_modified_on` cannot move for a value the
   merge did not store.
3. Update the characterization fixtures deliberately: the empty-description
   record, plus new cases for an empty scalar, an empty list, `False` and `0`,
   and an empty derived value. No other B04/B02a case changes.

## Why it is separate

B27 moves the merge with byte parity, so the B04 fixtures stay an unchanged
parity gate. Applying the grouped rule changes pinned results, so it gets its
own reviewable change. It resolves the conflict between B27's "tests pass
unchanged" and [artifacts.md](../../design/artifacts.md)'s merge rules.

## Done when

- A later empty description, title, salary or list no longer erases the stored
  value.
- A later non-empty value still replaces the stored one.
- `isActive=False` and numeric `0` still replace.
- A recomputed `language`/`guessed_required_languages` replaces even when empty.
- An empty or absent title/description does not move `last_modified_on`.
- The rest of the B04/B02a suite passes.
- New code passes `ruff` and `ty`; findings in untouched old code are reported,
  not fixed ([checks](../README.md#linting-and-typing)).

## Implementation notes

`postings_utils._has_value` is the existing definition of "has a value"; the
merge should share it rather than restate it. `CACHE_ALWAYS_FRESH_FIELDS` is the
existing always-fresh set and names the same four fields as the design.

Group membership lives in one place in `data/merge.py` (for example a tuple of
derived field names plus the always-fresh tuple), so B31's annotation fields
and B33's derivation cannot drift into different rules.
