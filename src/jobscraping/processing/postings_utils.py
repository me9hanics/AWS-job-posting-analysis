"""Utilities for filtering, comparing, and enriching postings data."""

import os
import re
from copy import deepcopy

from jobscraping.config.configs import RELATIVE_POSTINGS_PATH
from jobscraping.data.compare import get_added_and_removed as neutral_diff
from jobscraping.data.merge import ALWAYS_FRESH_FIELDS
from jobscraping.data.merge import has_value as _has_value
from jobscraping.io.files_io import load_file_if_str, load_list_items
from jobscraping.processing.attributes import (
    analyze_postings_language,
    find_keywords_in_postings,
    merge_matched_titlewords,
    rank_postings,
    salary_from_text,
)
from jobscraping.processing.language_requirements import guess_required_languages
from jobscraping.processing.transformations import (
    apply_filters_transformations as apply_filters_transformations_func,
)
from jobscraping.utils.datastruct_utils import get_nested_dict_keys

CACHE_ALWAYS_FRESH_FIELDS = set(ALWAYS_FRESH_FIELDS)
RAW_POSTING_FIELDS = {
    "title", "company", "description", "source", "salary", "salary_guessed",
    "salary_monthly_guessed", "locations", "first_collected_on", "last_collected_on",
    "collected_on", "timespan_days", "matched_titlewords", "date", "id", "url",
    "isActive", "isHomeOffice", "employmentTypes", "snippet", "role",
    "requirements", "nice_to_have", "benefits", "last_modified_on",
    "language", "guessed_required_languages",
}
INCOMPLETE_HISTORY_REPAIR_FIELDS = {
    "company",
    "description",
    "keywords",
    "language",
    "points",
}


def factual_postings(postings):
    """Project reusable facts; never carry profile fields into raw collection."""
    return {
        key: {field: deepcopy(value) for field, value in posting.items() if field in RAW_POSTING_FIELDS}
        for key, posting in postings.items()
    }


def validate_cache_mode(cache_mode):
    """Validate the currently supported posting cache modes."""
    if cache_mode not in (None, "id-only"):
        raise NotImplementedError(f"Cache mode is not implemented: {cache_mode}")


def split_cached_postings(
    postings,
    cached_postings=None,
    cache_mode=None,
    cache_hit_predicate=None,
):
    """Split discovered postings into reusable cache hits and processing misses.

    Non-empty freshly discovered fields override cached fields on hits. Collection
    metadata always comes from the fresh listing, while matched title words are
    merged. A custom predicate receives
    ``(posting_id, fresh_posting, cached_posting)`` and can refine the built-in
    ID-only policy, for example by allowing only complete records from selected
    sources.
    """
    validate_cache_mode(cache_mode)
    if cache_mode is None:
        return {}, postings

    cached_postings = cached_postings or {}
    hits = {}
    misses = {}
    for posting_id, posting in postings.items():
        cached_posting = cached_postings.get(posting_id)
        is_hit = cached_posting is not None
        if cache_hit_predicate is not None:
            is_hit = cache_hit_predicate(posting_id, posting, cached_posting)

        if is_hit:
            if cached_posting is None:
                raise ValueError(
                    "cache_hit_predicate returned True without a cached posting "
                    f"for {posting_id}"
                )
            reused = deepcopy(cached_posting)
            for field, value in posting.items():
                if field == "matched_titlewords":
                    continue
                if field in CACHE_ALWAYS_FRESH_FIELDS or _has_value(value):
                    reused[field] = deepcopy(value)
            merge_matched_titlewords(reused, posting)
            hits[posting_id] = reused
        else:
            misses[posting_id] = posting
    return hits, misses

def filter_postings(postings: dict, banned_words=None, banned_capital_words=None, **_kwargs):
    """Remove postings whose titles contain banned words."""
    banned_words = banned_words or []
    banned_capital_words = banned_capital_words or []
    filtered_postings = {}
    for _id, posting in postings.items():
        title = posting["title"]
        title_lower = title.lower()
        if any(word in title_lower for word in banned_words):
            continue
        if any(word in title for word in banned_capital_words):
            continue
        filtered_postings[_id] = posting
    return filtered_postings

def get_added_and_removed(new, previous):
    """Path-tolerant identity diff; ordering is left to the caller (Q16, B28).

    String arguments are read as dict-valued files. The diff itself is the
    neutral one in ``jobscraping.data.compare`` and adds no profile field.
    """
    new = load_file_if_str(new, "dict")
    previous = load_file_if_str(previous, "dict")
    return neutral_diff(
        new if isinstance(new, dict) else {},
        previous if isinstance(previous, dict) else {},
    )

def threshold_postings_by_points(postings, points_threshold = 0.01):
    """
    Filter a list of postings by a points threshold. If None, no filtering is applied.

    Parameters:
    postings (dict): The list of postings to filter.
    points_threshold (float): The points threshold to filter by.

    Returns:
    filtered_postings (dict): The filtered list of postings.
    """
    filtered_postings = {
        key: value
        for key, value in postings.items()
        if (points_threshold is None) or value.get("points", 0) >= points_threshold
    }
    return filtered_postings

def compare_postings(
    new=None,
    previous=None,
    print_attrs=("title", "company", "points"),
    printed_text_max_length=100,
    points_threshold=0.01,
    added=None,
    removed=None,
):
    """
    Compare two lists of postings and print out the differences.
    If new or previous is a string, the list is read from a file.
    If added or removed are given, they are used directly.

    Parameters:
    new (list | str): The new list of postings, optionally read from a file.
    previous (list | str): The previous list of postings, optionally read from a file.
    print_out_titles (bool): Whether to print out the titles of the postings.

    Returns:
    added (dict): The new postings that were added.
    removed (dict): The old postings that were removed.
    """
    if added is None or removed is None:
        if not (new or previous):
            raise ValueError("If added or removed are not given, new and previous must be given.")
        _added, _removed = get_added_and_removed(new, previous)
        added = added if added is not None else threshold_postings_by_points(_added, points_threshold)
        removed = removed if removed is not None else threshold_postings_by_points(_removed, points_threshold)

    print_out = print_attrs if print_attrs else "none"
    if print_out=="complete_lists":
        #make print out a list of all of the keys in the dictionaries, every single key that appears at least once
        print_out = list(
                    get_nested_dict_keys(new or added, appear="any", return_type=set).union(
                    get_nested_dict_keys(previous or removed, appear="any", return_type=set))
                    )
    elif print_out=="only_lengths":
        print("Amount of new items: ", len(added))
        print("Amount of removed items: ", len(removed))
    elif isinstance(print_out, str) and (print_out!="none"):
        # Interpreted as a key in the dictionaries in the two lists
        print_out = [print_out]

    print_added = added.copy()
    print_removed = removed.copy()

    if printed_text_max_length:
        print_added = {
            key: {
                k: v[:printed_text_max_length] + "..."
                if isinstance(v, str) and (len(str(v)) > printed_text_max_length)
                else v
                for k, v in value.items()
            }
            for key, value in added.items()
        }
        print_removed = {
            key: {
                k: v[:printed_text_max_length] + "..."
                if isinstance(v, str) and (len(str(v)) > printed_text_max_length)
                else v
                for k, v in value.items()
            }
            for key, value in removed.items()
        }

    if isinstance(print_out, (list, tuple, set)):
        print("New items above points threshold: ")
        for posting_key in print_added:
            text = ",\n\t".join(
                [
                    str(u) + ": " + str(v)
                    for u, v in (print_added[posting_key].items())
                    if u in print_out
                ]
            )
            print(f"\n{posting_key}: \n\t{text}")
        print("\n\n\nRemoved items above points threshold: ")
        for posting_key in print_removed:
            text = ",\n\t".join(
                [
                    str(u) + ": " + str(v)
                    for u, v in (print_removed[posting_key].items())
                    if u in print_out
                ]
            )
            print(f"\n{posting_key}: \n\t{text}")
    return added, removed

def unify_postings(
    postings=None,
    folder_path=f"{RELATIVE_POSTINGS_PATH}/tech/",
    extend=False,
    merge_with_history=False,
    history_filename="postings_history.json",
):
    """
    Compress multiple lists of postings into one list.
    If postings is a string, the list is read from a file.

    If extend=False, duplicates are merged into a single record and missing fields
    are filled in from newer entries. If extend=True, all versions are kept as a list
    per posting key, and global min/max dates are propagated to each version.

    By default every JSON file in ``folder_path`` is unified. If
    ``merge_with_history`` is True, only ``history_filename`` and the explicitly
    supplied ``postings`` dictionary are merged.

    Parameters:
    postings (list | *): The list of postings to combine - or overwritten if not a list.
    folder_path (str): The directory path to load the files from.
    extend (bool): Whether to extend the values of duplicate keys.
    merge_with_history (bool): Whether to merge only history plus ``postings``.
    history_filename (str): History file to use in targeted merge mode.

    Returns:
    all_postings (dict): The combined list of postings.
    """
    if merge_with_history:
        if not history_filename:
            raise ValueError("history_filename is required in targeted merge mode")
        files = []
        history_path = os.path.join(folder_path, history_filename)
        if os.path.exists(history_path):
            files.append(load_file_if_str(history_path, "dict"))
        if postings is not None:
            if isinstance(postings, str):
                postings = load_file_if_str(postings, "dict")
            if not isinstance(postings, dict):
                raise TypeError("postings must be a dictionary or JSON file path")
            files.append(postings)
    else:
        files = load_list_items(postings, folder_path=folder_path, type_="dict")

    all_postings = {}
    for postings_list in files:
        for key, value in postings_list.items():
            collected_on = value.get('collected_on', None)
            first_collected = value.get('first_collected_on', collected_on)
            first_collected = first_collected if first_collected and first_collected <= collected_on else collected_on
            last_collected = value.get('last_collected_on', collected_on)
            last_collected = last_collected if last_collected and last_collected >= collected_on else collected_on
            
            if key not in all_postings:
                all_postings[key] = value
                all_postings[key]['first_collected_on'] = first_collected
                all_postings[key]['last_collected_on'] = last_collected
            else:
                if not extend:
                    stored_posting = all_postings[key]
                    stored_last = stored_posting.get('last_collected_on')
                    incoming_is_not_older = (
                        not stored_last
                        or not last_collected
                        or last_collected >= stored_last
                    )
                    repair_incomplete_history = (
                        not stored_posting.get("description")
                        and bool(value.get("description"))
                        and incoming_is_not_older
                    )

                    #Update missing fields
                    for col, row in value.items():
                        if (col not in stored_posting.keys()) or (not stored_posting[col]):
                            stored_posting[col] = row

                    # A previously incomplete record may contain non-empty but
                    # invalid derived values, such as a title-only score. Replace
                    # those fields when a complete newer version is collected.
                    if repair_incomplete_history:
                        for col in INCOMPLETE_HISTORY_REPAIR_FIELDS:
                            if col in value and (
                                col != "company" or _has_value(value[col])
                            ):
                                stored_posting[col] = deepcopy(value[col])

                    #Merge matched_titlewords so duplicates keep all titleword hits
                    merge_matched_titlewords(all_postings[key], value)
                    
                    stored_first = stored_posting.get('first_collected_on')
                    if first_collected:
                        if not stored_first or first_collected < stored_first:
                            all_postings[key]['first_collected_on'] = first_collected
                    
                    stored_last = stored_posting.get('last_collected_on')
                    if last_collected:
                        if not stored_last or last_collected > stored_last:
                            all_postings[key]['last_collected_on'] = last_collected
                            #Update description to latest version
                            all_postings[key]["description"] = value.get(
                                "description",
                                all_postings[key].get("description", None),
                            )
                    
                else:  # extend==True
                    if not isinstance(all_postings[key], list):
                        all_postings[key] = [all_postings[key]]
                    value['first_collected_on'] = first_collected or all_postings[key][0].get('first_collected_on')
                    value['last_collected_on'] = last_collected or all_postings[key][0].get('last_collected_on')
                    all_postings[key].append(value)
                    
                    # Update global min/max across all versions
                    if first_collected or last_collected:
                        global_first = min(
                            (
                                v.get('first_collected_on')
                                for v in all_postings[key]
                                if v.get('first_collected_on')
                            ),
                            default=None,
                        )
                        global_last = max(
                            (
                                v.get('last_collected_on')
                                for v in all_postings[key]
                                if v.get('last_collected_on')
                            ),
                            default=None,
                        )

                        # Keep matched_titlewords consistent across versions
                        union_titlewords = []
                        for posting_store in all_postings[key]:
                            titlewords = posting_store.get("matched_titlewords")
                            if not titlewords:
                                continue
                            if not isinstance(titlewords, list):
                                titlewords = [titlewords]
                            for titleword in titlewords:
                                if titleword not in union_titlewords:
                                    union_titlewords.append(titleword)
                        
                        for posting_store in all_postings[key]:
                            posting_store['first_collected_on'] = global_first
                            posting_store['last_collected_on'] = global_last
                            if union_titlewords:
                                posting_store['matched_titlewords'] = list(union_titlewords)
                            if posting_store.get('last_collected_on') == global_last:
                                posting_store["description"] = value.get(
                                    "description",
                                    posting_store.get("description", None),
                                )
    
    return all_postings

def process_data(
    postings: dict,
    banned_words=None,
    banned_capital_words=None,
    filter_method:callable = filter_postings,
    language_analysis_method:callable=analyze_postings_language,
    rank_method:callable=rank_postings,
    keyword_finding_method:callable=find_keywords_in_postings,
    apply_filters_transformations:callable=apply_filters_transformations_func,
    description_key="description",
    transformations=None,
    **kwargs,
):
    """Apply filtering, language analysis, ranking, keywords, and transformations."""
    if transformations is None:
        transformations = []
    postings = filter_method(postings, banned_words=banned_words,
                             banned_capital_words=banned_capital_words, **kwargs)
    postings = language_analysis_method(postings, description_key=description_key, **kwargs)
    for posting in postings.values():
        posting["guessed_required_languages"] = guess_required_languages(
            f"{posting.get('title', '')}\n{posting.get(description_key, '')}"
        )
    postings = rank_method(postings, **kwargs)
    postings = keyword_finding_method(postings, description_key=description_key, **kwargs)
    postings = apply_filters_transformations(postings, transformations=transformations, **kwargs)
    return postings

def process_posting_soups(
    soups,
    pattern,
    website="",
    posting_id=False,
    posting_id_path=None,
    posting_id_regex=r'\d+',
    title_path=None,
    company_path=None,
    salary_path=None,
):
    """Extract postings from soup elements using selectors and regexes."""
    postings = {}
    for soup in soups:
        selects = soup.select(pattern)
        for select in selects:
            posting_id_value = None
            title = None
            company = None
            salary = None
            salary_versions = {}
            if title_path:
                title = select[title_path].text
            if company_path:
                company = select[company_path].text
            if salary_path:
                salary = select[salary_path].text
                salary_versions = salary_from_text(salary)
            if posting_id:
                if posting_id_path is None:
                    posting_id_value = re.search(posting_id_regex, select.text).group()
                else:
                    posting_id_value = re.search(posting_id_regex, select[posting_id_path]).group()
                if (posting_id_value is not None) and (posting_id_value in postings):
                    _text = select.text
                    if _text:
                        _text = _text.strip()
                    postings[posting_id_value] = {
                        "title": title,
                        "company": company,
                        "id": posting_id_value,
                        "source": website,
                        "salary": salary,
                        "salary_versions": salary_versions,
                        "text": _text,
                    }
            else:
                _text = select.text
                if _text:
                    _text = _text.strip()
                if _text and (_text not in postings):
                    postings[_text] = {
                        "title": title,
                        "company": company,
                        "id": None,
                        "source": website,
                        "salary": salary,
                        "salary_versions": salary_versions,
                        "text": _text,
                    }
    return postings
