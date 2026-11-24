# B19 — Give `KarriereAT` declared steps

Status: todo · Milestone: M4 Collector · Phase 4 · Size: M

- Depends on: B12, B16, B17, B18
- Files: `scrapers/websites/karriere_at.py`

## Do

1. Split the existing flow into two adapter functions, for example `listings`
   and `details`; use names that describe the site, not a global vocabulary.
2. Expose `steps = (Step("listings", listings), Step("details", details))`.
3. Keep the final facts identical to the pre-split flow.
4. Keep `gather_data` as a compatibility wrapper until B24 wires the collector;
   the step list is the new path.
5. Declare the steps as bound methods on the class, so per-run state (cookies,
   tokens) is available; import mechanics from `http`/`browser`/`pagination`/
   `parsing` and pass site differences as arguments or `rules` keys. Add no
   helper method to `BaseScraper` and override none (Q30).

## Done when

- A listings-only run returns identity/URL records.
- A full run returns the same facts as the B05 fixture baseline.
- No required/optional flag is introduced.
- The legacy entry point still calls the wrapper.
- The class inherits `BaseScraper` only for run context; the step methods are
  its only site-specific members.
