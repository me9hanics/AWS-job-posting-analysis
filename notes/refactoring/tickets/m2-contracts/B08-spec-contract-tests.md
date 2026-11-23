# B08 — Test the spec contract

Status: done · Milestone: M2 Contracts · Phase 1 · Size: S

- Depends on: B06, B07
- Files: `tests/test_specs.py` (new)

## Do

1. Missing required field is reported with the field name.
2. Unknown extra fields pass and are not removed.
3. `extend` returns a new spec and leaves the original untouched.
4. `check` does not mutate the input records.

## Done when

- The tests cover the four rules above and fail if `check` starts coercing.
