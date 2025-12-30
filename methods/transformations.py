from typing import List, Tuple, Callable
from collections.abc import Iterable
from copy import deepcopy
import re

def apply_filters_transformations(postings, transformations: List[Tuple[Callable, dict]] = [], **kwargs):
    """
    Apply a series of filter functions to postings.
    Parameters:
    postings: dict
        The postings to filter.
    filters: list of tuples
        Each tuple contains (function, kwargs_dict).
    Returns:
    filtered: dict
        The filtered postings.
    """
    transformed = postings
    for func, kwargs in transformations:
        transformed = func(transformed, **kwargs)
    return transformed

def pattern_match(
    text: str, terms: List[str], use_regex: bool,
    flags: int = 0, casefold: bool = False,
    logic_func: Callable[[Iterable[object]], bool] = any
) -> bool:
    """
    Returns True if any/all term/pattern matches the text.

    - If use_regex=True: uses re.search(term, text, flags=flags)
      If a regex is invalid, falls back to literal substring check.
    - If use_regex=False: uses substring check (optionally casefolded).
    Parameters:
    text: str                    The text to search within.
    terms: list of str           The terms or regex patterns to search for.
    use_regex: bool              Whether to treat terms as regex patterns.
    flags: int                   Regex flags to use if use_regex is True.
    casefold: bool               Whether to perform case-insensitive matching.
    logic_func: `any` or `all`   Function to aggregate matches (any or all).
    """
    if not terms:
        return False

    def _matches_one(term: str) -> bool:
        if use_regex:
            try:
                return re.search(term, text, flags=flags) is not None
            except re.error:
                haystack = text.casefold() if casefold else text
                needle = term.casefold() if casefold else term
                return needle in haystack

        haystack = text.casefold() if casefold else text
        needle = term.casefold() if casefold else term
        return needle in haystack

    return logic_func(_matches_one(t) for t in terms)

def select_keywords(postings, title_keywords=[], title_capital_keywords=[],
                    description_keywords=[], description_capital_keywords=[],
                    use_regex: bool = False, regex_flags: int = 0):
    title_keywords = title_keywords or []
    title_capital_keywords = title_capital_keywords or []
    description_keywords = description_keywords or []
    description_capital_keywords = description_capital_keywords or []

    filtered = {}
    for key, value in postings.items():
        title = value.get("title", "")
        description = value.get("description", "")

        if (
            pattern_match(title, title_keywords, use_regex=use_regex, flags=(regex_flags | re.IGNORECASE), casefold=True)
            or pattern_match(description, description_keywords, use_regex=use_regex, flags=(regex_flags | re.IGNORECASE), casefold=True)
            or pattern_match(title, title_capital_keywords, use_regex=use_regex, flags=regex_flags, casefold=False)
            or pattern_match(description, description_capital_keywords, use_regex=use_regex, flags=regex_flags, casefold=False)
        ):
            filtered[key] = value

    return filtered

def filter_out_keywords(postings, title_keywords=None, title_capital_keywords=None,
                        description_keywords=None, description_capital_keywords=None,
                        use_regex: bool = False, regex_flags: int = 0):
    title_keywords = title_keywords or []
    title_capital_keywords = title_capital_keywords or []
    description_keywords = description_keywords or []
    description_capital_keywords = description_capital_keywords or []

    filtered = postings.copy()
    for key, value in postings.items():
        title = value.get("title", "")
        description = value.get("description", "")

        if (
            pattern_match(title, title_keywords, use_regex=use_regex, flags=(regex_flags | re.IGNORECASE), casefold=True)
            or pattern_match(description, description_keywords, use_regex=use_regex, flags=(regex_flags | re.IGNORECASE), casefold=True)
            or pattern_match(title, title_capital_keywords, use_regex=use_regex, flags=regex_flags, casefold=False)
            or pattern_match(description, description_capital_keywords, use_regex=use_regex, flags=regex_flags, casefold=False)
        ):
            filtered.pop(key, None)

    return filtered

def filter_on_points(postings, min_points=0.01, default_points=0):
    filtered = {key: value for key, value in postings.items() if value.get('points', default_points) >= min_points}
    return filtered

def filter_on_date(postings, min_date=None, date_key='first_collected_on'):
    if min_date is None:
        return postings
    filtered = {}
    for key, value in postings.items():
        post_date = value.get(date_key)
        if post_date and post_date >= min_date:
            filtered[key] = value
    return filtered

def extra_points_if_missing_keywords(postings, keywords_points: List[Tuple[List[str], float]]):
    for key, value in postings.items():
        title = value.get('title', '').lower()
        description = value.get('description', '').lower()
        for keywords, point in keywords_points:
            if all(keyword not in title and keyword not in description for keyword in keywords):
                value['points'] = value.get('points', 0) + point
    return postings

def add_postings(postings:dict, candidate_postings:dict, select_ids = []):
    if not select_ids:
        #consider no-overwrite as option
        postings.update(candidate_postings)
    else:
        candidate_postings = deepcopy(candidate_postings)
        for id in select_ids:
            if id in candidate_postings:
                postings[id] = candidate_postings[id]
    return postings
