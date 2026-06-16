"""Skeleton for broad, profile-neutral scraping into a universal vault.

This module is intentionally not wired into the current runtime yet.

Future replacement scope:
- Some responsibilities from ``jobscraping.pipelines.collecting.scrape_sites``.
- Some orchestration currently embedded in profile scripts under ``schedule/``.

Not kept here from the old flow:
- Profile-specific scoring.
- Profile-specific filtering.
- Excel or Markdown output generation.
- Final profile current/newly-added files.
"""

from __future__ import annotations


def build_universal_scrape_inputs():
    """Build broad site/query inputs for the universal scrape.

    Planned responsibilities:
    - Combine titlewords/queries across profiles.
    - Deduplicate queries before scraping.
    - Keep enough metadata to know which query matched each posting.

    Placeholder only.
    """


def scrape_site_to_universal_chunks():
    """Run one site scraper and save resumable chunk outputs.

    Planned responsibilities:
    - Instantiate an existing site scraper such as KarriereAT or Raiffeisen.
    - Run a scrape for one site, query, location, or other restartable unit.
    - Save the chunk immediately.

    Placeholder only.
    """


def scrape_universal_postings():
    """Run the full broad scrape and return universal raw/current candidates.

    Planned responsibilities:
    - Loop over all configured site scrapers.
    - Call ``scrape_site_to_universal_chunks`` for restartable units.
    - Merge chunks into a single universal postings dictionary.

    Placeholder only.
    """


def merge_universal_chunks():
    """Merge previously saved universal scrape chunks.

    Planned responsibilities:
    - Load chunk files from the universal chunks folder.
    - Merge duplicate postings.
    - Preserve all matched scrape queries/titlewords.

    Placeholder only.
    """


def run_universal_scrape_flow():
    """Top-level universal scrape orchestration.

    Planned flow:
    1. Build broad scrape inputs.
    2. Scrape each restartable chunk.
    3. Merge chunk outputs.
    4. Hand the merged postings to universal storage helpers.

    Placeholder only.
    """
