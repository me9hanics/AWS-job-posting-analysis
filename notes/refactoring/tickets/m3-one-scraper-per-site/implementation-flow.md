# M3 implementation flow — one scraper per site

The milestone's own view of what B11–B18 build and where each piece sits. Tickets
run in order; each gets its own chain, with the mock shapes it introduces. Mock
code shows boundaries only — it is never imported or copied verbatim.

`In → Does → Out → Next`, per ticket. A ticket with unrelated parts gets one
chain per part; a ticket that builds one continuous segment gets one chain.

The design source for this milestone is
[module-seams.md](../../design/module-seams.md); the workstream is
[breakdown/collection.md](../../breakdown/collection.md). Two facts shape every
ticket below:

- The **canonical copies are in `sites.py`**, not in the split modules. The split
  modules are stale pre-B02a copies, so B12–B14 move *from* `sites.py` and the
  direction in their file lists is the destination, not the source.
- `scrape.py` ends the milestone as three modules plus a facade, and the facade is
  removed in B18 because nothing outside the package uses it. Tests that patch
  `scrape.requests` / `scrape.time` move with the functions.

---

## B11 — the canonical copies

- **In:** the three copy sets — `sites.py` (active), `basescraper.py`,
  `websites/karriere_at.py`, `websites/raiffeisen.py` (parallel) — and the B05
  fixtures under `tests/fixtures/`.
- **Does:** diff the copies; run the fixtures against `sites.py`; record which
  copy is canonical and why.
- **Out:** a decision table in `design/module-seams.md` plus the Q16 answer.
- **Next:** B12/B13 move the `sites.py` bodies out; B14 keeps the `sites.py`
  `BaseScraper`.

```text
sites.py::BaseScraper      canonical  date_day -> business_day via BUSINESS_DAY_SHIFT,
                                      process=False raw path, split_cached_postings,
                                      factual_postings
sites.py::KarriereAT       canonical  410 terminal status, stop condition,
                                      raise_on_http_error=not process, cache
sites.py::Raiffeisen       canonical  collected_on in listing, per-posting detail
                                      fetch when process=False
basescraper.py, websites/karriere_at.py, websites/raiffeisen.py
                           stale      no date_day, no process/cache support,
                                      BASE_Scraper business_day built differently
```

Q16, decided here because B12 moves the first caller: **no compatibility layer
beyond the move itself.** `sites.py` becomes a re-export while B12–B14 land and is
deleted in B15 together with the last importer. `collecting.get_postings` is not
touched by this milestone and keeps its wrapper question for B19/M4.

## B12 — `KarriereAT` to its site module

- **In:** `sites.py::KarriereAT` (canonical, unchanged) and
  `websites/karriere_at.py` (stale body to overwrite).
- **Does:** replace the site module body with the canonical class; export it;
  leave a re-export in `sites.py` so existing imports keep working.
- **Out:** one definition in `websites/karriere_at.py`; `sites.py` binds the same
  object.
- **Next:** B13 copies the same shape for `Raiffeisen`; B15 removes the
  `sites.py` binding.

```python
# src/jobscraping/scrapers/websites/karriere_at.py
class KarriereAT(BaseScraper):        # body moved verbatim from sites.py
    ...

# src/jobscraping/scrapers/websites/__init__.py
from jobscraping.scrapers.websites.karriere_at import KarriereAT

# src/jobscraping/scrapers/sites.py    (temporary, removed in B15)
from jobscraping.scrapers.websites.karriere_at import KarriereAT
```

## B13 — `Raiffeisen` to its site module

- **In:** `sites.py::Raiffeisen` (canonical) and the stale
  `websites/raiffeisen.py`.
- **Does:** same move; the stale module's `next_page_logic_by_length` import is
  carried from the canonical body.
- **Out:** one definition in `websites/raiffeisen.py`; `sites.py` re-export stays.
- **Next:** B14 has no site class left to keep.

```python
# src/jobscraping/scrapers/websites/raiffeisen.py
class Raiffeisen(BaseScraper):        # body moved verbatim from sites.py
    ...
```

## B14 — one `BaseScraper`, `sites.py` becomes a shim

- **In:** `sites.py::BaseScraper` (canonical) and `basescraper.py` (stale).
- **Does:** overwrite `basescraper.py` with the canonical body (including
  `BUSINESS_DAY_SHIFT`, `get_all_keywords` and the module-level scroll constants
  that copy carries); reduce `sites.py` to re-exports; point
  `scrapers/__init__.py` at the real modules.
- **Out:** three classes, one definition each; `scrapers/__init__.py` unchanged
  in public names.
- **Next:** B15 deletes `sites.py`; B16/B17 read this `BaseScraper` while splitting
  mechanics.

```python
# src/jobscraping/scrapers/basescraper.py
BUSINESS_DAY_SHIFT = 8 * 60 * 60
class BaseScraper:                    # canonical body, date_day included
    ...

# src/jobscraping/scrapers/sites.py    (shim; deleted in B15)
from jobscraping.scrapers.basescraper import BUSINESS_DAY_SHIFT, BaseScraper
from jobscraping.scrapers.websites import KarriereAT, Raiffeisen

# src/jobscraping/scrapers/__init__.py
from jobscraping.scrapers.basescraper import BaseScraper
from jobscraping.scrapers.websites import KarriereAT, Raiffeisen
__all__ = ["BaseScraper", "KarriereAT", "Raiffeisen"]
```

`tests/test_collection_cli.py` patches `jobscraping.scrapers.sites.time.time`; it
moves to `jobscraping.scrapers.basescraper.time.time` in this ticket, because the
patch only works on the module that defines `__init__`.

## B15 — the importers

- **In:** `sites` imported by `pipelines/collecting.py`,
  `processing/postings_utils.py`, `script.py`, `schedule/emails.py` and four test
  modules.
- **Does:** import the public names from `jobscraping.scrapers`; drop the unused
  `emails.py` import; delete `sites.py`.
- **Out:** no `scrapers.sites` anywhere; one import path for all callers.
- **Next:** B21/B29 have one place to remove the scraper dependency from.

```python
# src/jobscraping/pipelines/collecting.py
from jobscraping.scrapers import BaseScraper, KarriereAT, Raiffeisen
SCRAPERS = [KarriereAT, Raiffeisen]

# src/jobscraping/processing/postings_utils.py  (inside enrich_postings)
from jobscraping.scrapers import BaseScraper

# src/jobscraping/processing/postings_utils.py must not gain module-level
# scraper imports; the function-local import stays until B29.
```

## B16 — the HTTP path

- **In:** `scrape.py`'s request functions and the test doubles that patch
  `scrape.requests.Session`.
- **Does:** move `requests_responses` and `requests_responses_with_cookies` into
  `http.py` unchanged; re-export them from `scrape.py`.
- **Out:** `scrapers/http.py` with no Selenium import.
- **Next:** B17 moves the browser half; B18 points site modules at `http`
  directly.

```python
# src/jobscraping/scrapers/http.py
def requests_responses(urls, return_kind="responses", https=False, headers=None,
                       wait_time=0.3, timeout=None, verbose=False): ...
def requests_responses_with_cookies(base_url, pages, base_path, referer=None, ...): ...

# src/jobscraping/scrapers/scrape.py   (facade)
from jobscraping.scrapers.http import (        # noqa: F401
    requests_responses, requests_responses_with_cookies,
)
def process_site_urls(urls, usecase="http", **kwargs): ...   # moves in B17
```

New test: one direct `http.requests_responses` call against a fake session, so
the request/parse path is covered without the scraper classes.

## B17 — the headless-browser path

- **In:** `scrape.py`'s Selenium functions, `_require_selenium`, and the
  `process_site_urls` dispatcher that reaches into both halves.
- **Does:** move `press_button_until_gone`, `close_popup`, `scroll_scrape_website`,
  `scroll_scrape_websites`, `close_website_popup`, `load_page`, `load_pages` and
  the scroll constants into `browser.py`; move `process_site_urls` into `http.py`
  with a function-local `browser` import for its Selenium branches, marked as a
  transitional shim rather than an intended design.
- **Out:** `browser.py` with no `requests` use; `http.py` that still imports no
  Selenium at module level.
- **Next:** B18 removes the facade; `process_site_urls` keeps working for any
  future caller.

```python
# src/jobscraping/scrapers/browser.py
def close_website_popup(driver, button_selector, url=None, ...): ...
def load_page(url, driver=None, close_popup=True, ...): ...
def load_pages(urls, close_popup="first", ...): ...

# src/jobscraping/scrapers/http.py
def process_site_urls(urls, usecase="http", **kwargs):
    # TRANSITIONAL: this dispatch mixes the HTTP and browser paths. HTTP scraping
    # (and therefore http.py) must not contain Selenium; a headless-browser fetch
    # path is expected to replace this. Kept only until that path exists.
    if usecase in ("http", "https"): ...
    if usecase == "selenium":
        from jobscraping.scrapers import browser      # local: keeps http Selenium-free
        return browser.scroll_scrape_websites(urls, **kwargs)
```

`_load_page` in `BaseScraper` calls `scrape.load_page(driver, url, ...)` while the
helper's first parameter is `url`. That mismatch predates this milestone and is
unreachable for the two active sites (both use `usecase="http"/"https"`); the move
keeps it verbatim and does not "fix" it here.

## B18 — pagination, and the facade retires

- **In:** `next_page_logic_by_length` and the `scrape` module reference held by
  `basescraper.py` and the two site modules.
- **Does:** move the helper to `pagination.py`; point site modules and
  `BaseScraper` at `http`, `browser` and `pagination`; delete `scrape.py`; retarget
  the four test modules that patch it.
- **Out:** `scrape.py` gone; no site module or base class holds HTTP/session code.
- **Next:** B19/B20 turn these modules' `gather_data` into declared steps.

```python
# src/jobscraping/scrapers/pagination.py
def next_page_logic_by_length(data: BeautifulSoup, pattern: str, lengths: list) -> bool: ...

# src/jobscraping/scrapers/websites/raiffeisen.py
from jobscraping.scrapers import http, pagination
result = http.requests_responses([url], https=(usecase == "https"),
                                 return_kind="soups", wait_time=request_wait_time,
                                 verbose=verbose)
get_next_page = pagination.next_page_logic_by_length(soup, titles_pattern,
                                                    lengths=[25, 50])
```

Tests move with the functions: `patch.object(scrape.requests, "Session", ...)`
becomes `patch.object(http.requests, "Session", ...)`, and
`patch.object(scrape.time, "sleep")` becomes `patch.object(http.time, "sleep")`.
One added test (B16, `HttpRequestParsingTests`) covers the request/parse path;
B18 adds none. The "HTTP code does not touch Selenium" invariant is source-level:
`rg -n "^\s*(from|import)\s+selenium" src/jobscraping/scrapers/http.py` → none
(the word `selenium` still appears there only as a `usecase` literal). A
subprocess `sys.modules` assertion cannot hold, because importing the submodule
executes `scrapers/__init__.py`, which imports `BaseScraper`, and
`basescraper.py` imports `webdriver` inside a `try/except` — so `selenium` is in
`sys.modules` whenever it is installed.

---

## The milestone end to end

After B11–B18 the mechanics and the site bodies exist independently; nothing has
changed about what a caller gets from `gather_data`:

```text
collecting.SCRAPERS = [KarriereAT, Raiffeisen]           (B15)
  -> adapter instantiated with rules/keywords/date_day    (B12/B13, BaseScraper B14)
  -> adapter calls http.requests_responses(_with_cookies) (B16)
     or browser.load_pages                                (B17)
  -> adapter parses payload -> postings dict
  -> Process=False path returns factual_postings          (unchanged)
  -> pagination.next_page_logic_by_length for next pages  (B18)
  -> postings dict to the profile pipeline                (unchanged)
```

What is fixed in place: one definition per class; one import path
(`jobscraping.scrapers`); mechanics split HTTP / browser / pagination with no
cross-import at module level; no `scrape.py`; site bodies untouched apart from
their imports.

## Where this leads (M4)

M3 does not introduce the step contract; it makes the place that will hold it.
B19/B20 turn the two classes moved here into adapters by adding a `source`
attribute and an ordered `steps` tuple, and by turning `gather_data` into
`listings`/`details` callables. `BaseScraper` survives that step as run context
only — config normalization, `day`/`business_day`, `source`, `steps` — one copy,
with no overridable hooks; the mechanics M3 splits out (`http`, `browser`,
`pagination`, `parsing`) are what sites call, and per-site differences are
arguments or `rules` keys (Q30,
[module-seams.md](../../design/module-seams.md#site-class-and-its-base)). The
adapter is the site class, not a replacement for the base class, and it stops
being a copy of it.

So nothing built in B11–B18 is throwaway: the site module created here is the
module the adapter list describes. What M3 deliberately does not do — leave
`gather_data` monolithic, keep `process` and the profile helpers on `BaseScraper`
— is removed by B19/B20/B31, not re-done.

## Gates for the milestone

- `uv run python -m unittest discover -s tests` → `OK`; the runner reports 114
  tests in this working tree — 84 tracked test methods plus 30 from untracked WIP
  test modules (`test_dani_profile.py`, `test_language_requirements.py`,
  `test_raw_collection.py`). Exactly one test was added in M3 (B16,
  `HttpRequestParsingTests`); none in B18.
- `rg "class BaseScraper|class KarriereAT|class Raiffeisen" src` → three matches,
  after B14.
- `rg "scrapers import sites|scrapers\.sites"` → no matches, after B15.
- `rg "from selenium|import selenium" src/jobscraping/scrapers/http.py` → no
  Selenium import, after B17.
- `rg "scrape\.py|from jobscraping.scrapers import scrape"` → no matches, after
  B18.
- Ticket status rows in [tickets/README.md](../README.md) updated in the same
  change as each ticket. Work stays in the working tree: no commits for B11–B18.

One accepted wrinkle: `http.py` ends the milestone with `process_site_urls`,
whose Selenium branch imports `browser` lazily. It is a transitional shim, not the
intended design — HTTP scraping should not contain Selenium, and the headless
fetch path is expected to move out of `http.py` once it exists. The comment in the
function says so.
