def sort_dict_by_key(x, key="points", descending=True, default=0):
    return {k: v for k, v in sorted(x.items(), key=lambda item: item[1].get(key, default
                                                                            ) if item[1].get(key) is not None else default,
                                    reverse=descending)} if x else {}

def reorder_dict(d, keys_order, nested=False):
    return {k: d[k] for k in keys_order if k in d} if not nested else {
        k: reorder_dict(d[k], keys_order, nested=False) for k in d.keys()
    }

def get_nested_dict_keys(dictionary, appear = "any", return_type=list):
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