"""Skeleton for profile output orchestration.

This module is intentionally not wired into the current runtime yet.

Future replacement scope:
- High-level output orchestration from ``methods.outputs.generate_outputs``.
- Markdown logging calls currently made directly in ``schedule/*_collect.py``.

Not kept here from the old flow:
- Excel rendering internals, which belong in ``methods.outputs_excel``.
- Scraping, storage, scoring, or filtering.
"""

from __future__ import annotations


def generate_excel_output_for_profile():
    """Generate a profile Excel output.

    Planned responsibilities:
    - Prepare profile-selected postings for Excel.
    - Call Excel-specific helpers in ``methods.outputs_excel``.

    Placeholder only.
    """


def generate_markdown_log_for_profile():
    """Generate or update a profile Markdown log.

    Placeholder only.
    """


def generate_email_output_for_profile():
    """Generate or send a profile email output.

    Placeholder only.
    """


def generate_profile_outputs():
    """Top-level output orchestration for selected profile postings.

    Planned flow:
    1. Receive selected current postings and newly-added postings.
    2. Generate configured output types.
    3. Return generated artifact paths.

    Placeholder only.
    """
