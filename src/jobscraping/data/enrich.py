"""Rerunnable, profile-neutral enrichment of posting records.

Salary guesses, collection dates and the annotation fields are facts any
profile would compute the same way, so they live here and need no scraper,
browser or network. Profile policy reprocessing stays in ``processing``.
"""

import datetime
import os
import re
from typing import cast

from jobscraping.data.language import analyze_text_language, guess_required_languages
from jobscraping.data.merge import has_value
from jobscraping.data.salary import salary_from_description, salary_from_text
from jobscraping.io.files_io import load_file_if_str


def annotate_postings(postings, description_key="description") -> dict:
    """Fill ``language`` and ``guessed_required_languages``; replace, never merge.

    Only a record with a non-empty description is annotated. Rerunning the pass
    overwrites the same two keys, so two runs produce identical records.
    """
    for posting in postings.values():
        description = posting.get(description_key)
        if not has_value(description):
            continue
        posting["language"] = analyze_text_language([description])[0]
        posting["guessed_required_languages"] = guess_required_languages(
            f"{posting.get('title', '')}\n{description}"
        )
    return postings


def get_date_of_collection(value=None, filename=None, overwrite=False):
    """Infer collection date from a posting or filename when possible."""
    if not overwrite and isinstance(value, dict) and ('collected_on' in value) and value['collected_on']:
        return value['collected_on']
    if filename and isinstance(filename, str):
        match = re.search(r'20\d{2}-\d{2}-\d{2}', filename)
        if match:
            return match.group()
    if filename and isinstance(filename, str) and os.path.exists(filename):
        return str(datetime.datetime.fromtimestamp(os.path.getctime(filename)).date())
    return None


def enrich_postings(postings: dict | str, *, overwrite=True, filename=None) -> dict:
    """Add salary guesses, ``collected_on`` and the neutral annotations."""
    if isinstance(postings, str):
        filename = filename or postings
    postings = cast(dict, load_file_if_str(postings, type_="dict"))
    for posting in postings.values():
        if 'salary' in posting:
            salary_read = salary_from_text(posting['salary'])
        else:
            salary_read = salary_from_description(posting.get("description", []))
        if overwrite or ('salary_guessed' not in posting) or (not posting['salary_guessed']):
            posting['salary_guessed'] = salary_read
        if overwrite or ('salary_monthly_guessed' not in posting) or (not posting['salary_monthly_guessed']):
            posting['salary_monthly_guessed'] = salary_read["monthly"] if salary_read else None

        if 'collected_on' not in posting or (not posting['collected_on']): #don't overwrite
            posting['collected_on'] = get_date_of_collection(value=posting, filename=filename, overwrite=False)

    return annotate_postings(postings)
