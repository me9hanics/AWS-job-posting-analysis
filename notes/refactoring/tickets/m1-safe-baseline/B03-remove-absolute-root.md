# B03 — Remove the absolute repository root

Status: done · Milestone: M1 Safe baseline · Phase 0 · Size: S

- Depends on: B02
- Files: `src/jobscraping/config/configs.py`, `tests/`

## Do

1. Replace the hardcoded `REPO_ROOT_PATH` with a value derived from `__file__`,
   for example `Path(__file__).resolve().parents[3]`.
2. Keep the derived absolute value only at runtime; do not commit a path.
3. Add one test that asserts `<root>/pyproject.toml` exists. Do not assert on
   string formatting; the point is that the root resolves to the repository.
4. Run the suite and an import from a different working directory.

## Done when

- A drive-letter or home-directory path pattern finds nothing in `src tests`
  (`rg "[A-Za-z]:[\\/]|/home/|/Users/" src tests`).
- The test suite passes.
- `config` imports from a directory other than the repository root.

## Why first

Every later path change is easier when the root is already relative and portable.
This is the only runtime change in milestone M1.
