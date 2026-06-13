"""Utilities for sorting and restructuring dictionaries."""
from typing import Any, Callable, Dict, List, Tuple

def sort_dict_by_key(
    data: Dict,
    key: str = "points",
    descending: bool = True,
    default: Any = 0,
) -> Dict:
    """Sort a dict of dicts by a nested key, and return a new dict."""
    if not data:
        return {}

    def _sort_value(item: Tuple) -> Any:
        value = item[1].get(key, default)
        return value if value is not None else default

    return dict(sorted(data.items(), key=_sort_value, reverse=descending))

def reorder_dict(
    data: Dict,
    keys_order: List,
    nested: bool = False,
) -> Dict:
    """Reorder dict keys; optionally reorder nested dict values."""
    if not nested:
        return {k: data[k] for k in keys_order if k in data}
    return {k: reorder_dict(data[k], keys_order, nested=False) for k in data}

def get_nested_dict_keys(
    dictionary: Dict,
    appear: str = "any",
    return_type: Callable = list,
) -> Any:
    """
    Get the keys of a nested dictionary: for each key, take the value dictionary and return
            the union or intersection of these nested dictionaries.

    Parameters:
    dictionary (dict): The input dictionary, with dictionaries as values.
    appear (str): Whether to return the keys that appear in all or any of the nested dictionaries.
        -"all": Return the keys that appear in all nested dictionaries.
        -"any": Return the keys that appear at least once in the nested dictionaries.
    return_type (type): The type of the output. Typically list or set.
    """
    #plan: make it handle different levels, e.g. 2 levels deep vs. 3 levels deep (with while)
    if len(dictionary) == 0:
        try:
            return return_type([])
        except TypeError:
            return []
    keys = set(dictionary[list(dictionary.keys())[0]].keys())
    for _, value in dictionary.items():
        if appear == "all":
            keys = keys.intersection(set(value.keys()))
        elif appear == "any":
            keys = keys.union(set(value.keys()))
        else:
            raise ValueError("appear must be 'all' or 'any'")

    return return_type(keys)
