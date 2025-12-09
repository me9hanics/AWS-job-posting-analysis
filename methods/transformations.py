from typing import List, Tuple, Callable
from copy import deepcopy

def apply_filters_transformations(postings, transformations: List[Tuple[Callable, dict]] = []):
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

def select_keywords(postings, title_keywords=[], title_capital_keywords=[],
                    description_keywords=[], description_capital_keywords=[]):
    filtered = {}
    for key, value in postings.items():
        title = value.get('title', '').lower()
        description = value.get('description', '').lower()
        if any(term.lower() in title for term in title_keywords) or \
           any(term.lower() in description for term in description_keywords) or \
           any(term in title for term in title_capital_keywords) or \
           any(term in description for term in description_capital_keywords):
            filtered[key] = value
    return filtered

def filter_out_keywords(postings, title_keywords=[], title_capital_keywords=[],
                         description_keywords=[], description_capital_keywords=[]):
    filtered = postings.copy()
    for key, value in postings.items():
        title = value.get('title', '')
        description = value.get('description', '')
        if any(term.lower() in title.lower() for term in title_keywords) or \
           any(term.lower() in description.lower() for term in description_keywords) or \
           any(term in title for term in title_capital_keywords) or \
           any(term in description for term in description_capital_keywords):
            filtered.pop(key, None)
    return filtered

def filter_on_points(postings, min_points=0.01, default_points=0):
    filtered = {key: value for key, value in postings.items() if value.get('points', default_points) >= min_points}
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
        #TODO check
        postings.update(candidate_postings)
    else:
        candidate_postings = deepcopy(candidate_postings)
        for id in select_ids:
            if id in candidate_postings:
                postings[id] = candidate_postings[id]
    return postings
