# B19 — Give `KarriereAT` declared steps

Status: done · Milestone: M4 Collector · Phase 4 · Size: M

- Depends on: B12, B16, B17, B18
- Files: `scrapers/websites/karriere_at.py`, `scrapers/steps.py`

## Do

1. Split the existing flow into two adapter functions, for example `listings`
   and `details`; use names that describe the site, not a global vocabulary.
2. Expose `steps = (Step("listings", listings), Step("details", details))`.
3. Keep the final facts identical to the pre-split flow.
4. Keep `gather_data` as a compatibility wrapper; the step list is the new
   path. B24 stops the universal path from calling the wrapper; the legacy
   profile path keeps it until B44.
5. Declare the steps as bound methods on the class, so per-run state (cookies,
   tokens) is available; import mechanics from `http`/`browser`/`pagination`/
   `parsing` and pass site differences as arguments or `rules` keys. Add no
   helper method to `BaseScraper` and override none (Q30).

## Implementation notes

The raw half of `gather_data` becomes the step path; the `process=True` half
stays untouched until the legacy profile path is removed. Concretely:

- `listings` reads `self.keywords["titlewords"]`/`["locations"]` (the adapter
  owns its URL dialect) and reproduces today's `process=False` request flags:
  `terminal_http_statuses=(410,)`, `raise_on_http_error=True`,
  `raise_on_retry_failure=False`.
- `details` owns cache reuse: it calls `split_cached_postings` with
  `config.cached_postings`, `config.cache_mode` and
  `config.cache_hit_predicate`, fetches only the misses, and returns hits plus
  misses. A listings-only run therefore does not merge cached facts — the
  narrowest possible behaviour change, and no caller runs that combination.
- Delete the `_salary_from_text` override; call
  `processing.attributes.salary_from_text` with the site keywords and
  `conversion_rate=14`.
- `CollectionConfigLike` gains `cached_postings` and `cache_hit_predicate` in
  this ticket, because `details` is their first reader; B22 supplies the
  concrete values on `CollectionConfig`.
- `gather_data` keeps its signature and its `process=True` body and delegates
  `process=False` to the steps plus `factual_postings`. It remains until the
  legacy path is removed (B44), so it is the one retained base-name override.
- Add `source = "karriere.at"` and the `steps` tuple in `__init__`; declare
  `DISCOVERED_POSTINGS`/`COLLECTED_POSTINGS` on the steps.

The flow, the mocks and the cache decision are in
[implementation-flow.md](implementation-flow.md#b19--karriereat-declared-steps)
and [design/collection-steps.md](../../design/collection-steps.md#execution-rules).

## Done when

- A listings-only run returns identity/URL records.
- A full run returns the same facts as the B05 fixture baseline.
- No required/optional flag is introduced.
- The legacy entry point still calls the wrapper.
- The class inherits `BaseScraper` only for run context; apart from the
  temporary `gather_data` wrapper, the step methods are its only site-specific
  members.
