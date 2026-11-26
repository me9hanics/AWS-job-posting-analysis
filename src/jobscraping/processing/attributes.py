"""Helpers for job posting attributes: scoring, keyword analysis and policy.

Salary and text-language detection moved to ``data.salary`` and
``data.language``; the names below are transitional re-exports and B44 removes
the indirection.
"""

import re
from typing import Any, Callable, Dict, List

from jobscraping.data.language import analyze_text_language
from jobscraping.data.merge import merge_matched_titlewords
from jobscraping.data.salary import (
    DEFAULT_DESCRIPTION_REGEXES,
    DEFAULT_SALARY_KEYWORDS,
    DEFAULT_SALARY_REGEXES,
    salary_from_description,
    salary_from_text,
    salary_number_from_str,
    salary_regex,
)

__all__ = [
    "DEFAULT_DESCRIPTION_REGEXES",
    "DEFAULT_SALARY_KEYWORDS",
    "DEFAULT_SALARY_REGEXES",
    "add_matched_titleword",
    "analyze_postings_language",
    "analyze_text_language",
    "check_locations",
    "find_keywords",
    "find_keywords_in_postings",
    "merge_matched_titlewords",
    "rank_postings",
    "salary_from_description",
    "salary_from_text",
    "salary_number_from_str",
    "salary_points",
    "salary_regex",
    "score_text_nested",
]


def salary_points(
    salary,
    root_value=None,
    salary_ratio=0.15/100,
    high_dropoff=True,
    dropoff_bearable_ratio=1.25, #better at around 1.4
):
    """Calculate salary-based score, with optional dropoff."""
    if not root_value:
        root_value = 5000
    points = (salary - root_value) * salary_ratio
    if high_dropoff & (salary > root_value * dropoff_bearable_ratio):
        max_points = (root_value * dropoff_bearable_ratio - root_value) * salary_ratio
        points = 2 * max_points - points
    return points

def check_locations(locations: List, locations_desired: List):
    """Check if any desired location is present in the given locations list."""
    if locations and locations_desired:
        for location in locations:
            for desired in locations_desired:
                if desired.lower() in location.lower(): #in the string, e.g. "wien" in "wien 04"
                    return True
    return False

def score_text_nested(text: str, rules: dict) -> float:
    """
    Recursively score text based on nested regex pattern rules.

    Parameters:
    text: str
        The text to score.
    rules: dict
        Nested dictionary containing regex patterns and their scores.

    Returns:
    float: The total score for the text.
    """
    score = 0.0
    for _key, value in rules.items():
        if isinstance(value, dict):
            if "patterns" in value:
                flags = value.get("flags", 0)
                matches = []
                for pattern, pts in value["patterns"].items():
                    if re.search(pattern, text, flags=flags):
                        matches.append(pts)
                score += max(matches, default=0) if value.get("aggregation") == "max" else sum(matches)
            else:
                #Check nested dict
                score += score_text_nested(text, value)
    return score

def rank_postings(
    postings: dict,
    keyword_points=None,
    desc_ratio=0.3,
    root_value=5000,
    salary_ratio=0.15/100,
    dropoff_bearable_ratio=1.4,
    overwrite=True,
    locations_desired: List | None = None,
    locations_secodary: List | None = None,
    **_kwargs,
):
    """
    Rank postings using regex-based scoring system.
    
    Parameters:
    postings: dict
        Dictionary of job postings to rank.
    keyword_points: dict
        Nested dictionary with regex patterns and scores.
    desc_ratio: float
        Ratio to apply to description scores (title gets full weight).
    root_value: int
        Root salary value for scoring.
    salary_ratio: float
        Ratio for salary scoring.
    dropoff_bearable_ratio: float
        Ratio at which salary scoring starts to drop off.
    overwrite: bool
        If True, overwrite existing points.
    locations_desired: list
        List of desired locations.
    locations_secodary: list
        List of secondary locations.
        
    Returns:
    dict: Updated postings with points added.
    """
    if not keyword_points:
        keyword_points = {}

    if locations_desired is None:
        locations_desired = []
    if locations_secodary is None:
        locations_secodary = []

    for posting_id, posting in postings.items():
        if not overwrite and ("points" in posting.keys()) and posting["points"] is not None:
            continue

        title = posting.get("title", "")
        description = posting.get("description", "")
        salary = posting.get("salary_monthly_guessed")

        title_points = score_text_nested(title, keyword_points)
        description_points = score_text_nested(description, keyword_points) * desc_ratio

        points = title_points + description_points
        if salary:
            points += salary_points(
                salary,
                root_value=root_value,
                salary_ratio=salary_ratio,
                high_dropoff=True,
                dropoff_bearable_ratio=dropoff_bearable_ratio,
            )

        if posting.get("locations"):
            if not check_locations(posting["locations"], locations_desired=locations_desired):
                points -= 1
                if not check_locations(posting["locations"], locations_desired=locations_secodary):
                    points -= 1

        postings[posting_id]["points"] = round(points, 2)

    return postings

def find_keywords(
    text: str,
    keywords_list: List[str],
    case_sensitive=False,
    **_kwargs,
) -> List[str]:
    """
    Find keywords in text from a predefined list.
    
    Parameters:
    text: str
        The text to search in.
    keywords_list: list
        List of keywords to search for.
    sort: bool
        If True, return in the order they appear in keywords_list (already sorted by importance).
        
    Returns:
    list: List of matched keywords.
    """
    if not keywords_list:
        return []

    found = []
    if not case_sensitive:
        text = text.lower()

    for keyword in keywords_list:
        if not case_sensitive:
            keyword = keyword.lower()
        if keyword in text:
            found.append(keyword)

    return found

def find_keywords_in_postings(
    postings: dict,
    ordered_keywords: List | Dict,
    overwrite=True,
    sort=True,
    method: Callable[[str, list, list, bool, dict], List[Any]] = find_keywords,
    description_key="description",
    **_kwargs,
):
    """Find keywords inside each posting and store them under the posting dict."""
    if isinstance(ordered_keywords, dict):
        ordered_keywords = list(ordered_keywords.keys())

    case_sensitive_keywords = [
        kw for kw in ordered_keywords if any(c.isupper() for c in kw)
    ]
    case_insensitive_keywords = [
        kw for kw in ordered_keywords if not any(c.isupper() for c in kw)
    ]

    for posting_id, posting in postings.items():
        if overwrite or ("keywords" not in posting.keys()) or (not posting["keywords"]):
            postings[posting_id]["keywords"] = []
            if description_key in posting.keys():
                text = posting[description_key]
                keywords = method(text, keywords_list=case_sensitive_keywords,
                                  case_sensitive=True, sort=sort)
                keywords.extend(
                    method(
                        text,
                        keywords_list=case_insensitive_keywords,
                        case_sensitive=False,
                        sort=sort,
                    )
                )
                # Preserve order while de-duplicating.
                postings[posting_id]["keywords"] = list(dict.fromkeys(keywords))
    return postings

def add_matched_titleword(posting_data, titleword):
    """Add a titleword to a posting, avoiding duplicates."""
    if not titleword:
        return posting_data
    matched = posting_data.get("matched_titlewords")
    if not matched:
        posting_data["matched_titlewords"] = [titleword]
    elif titleword not in matched:
        matched.append(titleword)
    return posting_data


def analyze_postings_language(
    postings: Dict,
    description_key="description",
    **_kwargs,
) -> Dict:
    """Annotate postings with detected language based on description text."""
    descriptions = [posting.get(description_key, "") for posting in postings.values()]
    languages = analyze_text_language(descriptions)
    for key, lang in zip(postings.keys(), languages):
        postings[key]["language"] = lang
    return postings
