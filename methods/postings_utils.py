from methods.macros import *
from methods.files_io import load_file_if_str, load_list_items
import re
import os
from datetime import datetime
from typing import List, Dict

def sort_dict_by_key(x, key="points", descending = True):
    return {k: v for k, v in sorted(x.items(), key=lambda item: item[1][key], reverse = descending)} if x else {}

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

def get_date_of_collection(value=None, filename=None, overwrite=False):
    if not overwrite and isinstance(value, dict) and ('collected_on' in value) and value['collected_on']:
        return value['collected_on']
    if filename and isinstance(filename, str):
        match = re.search(r'202\d{1}-\d{2}-\d{2}', filename)
        if match:
            return match.group()
    if filename and isinstance(filename,str) and os.path.exists(filename):
        return str(datetime.fromtimestamp(os.path.getctime(filename)).date())
    return None

def get_added_and_removed(new, previous):
    """
    Compare two lists and return the differences.
    (If any of the lists are given as a string, it is interpreted as a file path,
            and the list is loaded from the file.)

    Parameters:
    new (list | str): The new list, that is being compared.
    previous (list | str): The previous list, to compare against.
    print_out (str): What to print out, if anything. Can be:
        -"complete_lists": Print out the lists
        -"only_lengths": Print out the lengths of the lists
        -"none": Do not print out anything
        -*string*: Interpreted as a key in dictionaries;
                print out the value of that key for each item in both lists.
    """
    new = load_file_if_str(new, "dict")
    previous = load_file_if_str(previous, "dict")
    added_keys = list(set(new) - set(previous))
    removed_keys = list(set(previous) - set(new))
    added = {key: new[key] for key in added_keys}
    removed = {key: previous[key] for key in removed_keys}
    added = sort_dict_by_key(added, key="points", descending = True) if added else {}
    removed = sort_dict_by_key(removed, key="points", descending = True) if removed else {}
    return added, removed

def threshold_postings_by_points(postings, points_threshold = 0.01):
    """
    Filter a list of postings by a points threshold. If None, no filtering is applied.

    Parameters:
    postings (dict): The list of postings to filter.
    points_threshold (float): The points threshold to filter by.

    Returns:
    filtered_postings (dict): The filtered list of postings.
    """
    filtered_postings = {key: value for key, value in postings.items() if (points_threshold == None) or value.get("points", 0) >= points_threshold}
    return filtered_postings

def compare_postings(new = [], previous = [], print_attrs=["title", "company", "points"], printed_text_max_length = 100,
                     points_threshold = 0.01, added=None, removed=None):
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
    if not added or not removed:
        if not (new or previous):
            raise ValueError("If added or removed are not given, new and previous must be given.")
        _added, _removed = get_added_and_removed(new, previous)
        added = added or threshold_postings_by_points(_added, points_threshold)
        removed = removed or threshold_postings_by_points(_removed, points_threshold)
    
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
    elif (type(print_out)==str) & (print_out!="none"):
        """Interpreted as a key in the dictionaries in the two lists"""
        print_out = [print_out]

    print_added = added.copy()
    print_removed = removed.copy()

    if printed_text_max_length:
        print_added = {key: {k: v[:printed_text_max_length]+"..." if isinstance(v, str) & (len(str(v))> printed_text_max_length)
                       else v for k,v in value.items()} for key, value in added.items()}
        print_removed = {key: {k: v[:printed_text_max_length]+"..." if isinstance(v, str) & (len(str(v))> printed_text_max_length)
                         else v for k,v in value.items()} for key, value in removed.items()}

    if type(print_out) == list:
        print("New items above points threshold: ")
        for posting_key in print_added:
            text = ",\n\t".join([str(u)+": "+str(v) for u,v in (print_added[posting_key].items()) if u in print_out])     
            print(f"\n{posting_key}: \n\t{text}")
        print("\n\n\nRemoved items above points threshold: ")
        for posting_key in print_removed:
            text = ",\n\t".join([str(u)+": "+str(v) for u,v in (print_removed[posting_key].items()) if u in print_out])
            print(f"\n{posting_key}: \n\t{text}")
    return added, removed

def unify_postings(postings=None, folder_path=f"{RELATIVE_POSTINGS_PATH}/tech/", extend = False):
    """
    Compress multiple lists of postings into one list.
    If postings is a string, the list is read from a file.

    Parameters:
    postings (list | *): The list of postings to combine - or overwritten if not a list.
    folder_path (str): The directory path to load the files from.
    extend (bool): Whether to extend the values of duplicate keys.

    Returns:
    all_postings (dict): The combined list of postings.
    """
    files = load_list_items(postings, folder_path=folder_path, type_="dict")

    all_postings = {}
    for postings in files:
        for key, value in postings.items():
            collected_on = value.get('collected_on', None)
            if key not in all_postings:
                all_postings[key] = value
                all_postings[key]['first_collected_on'] = collected_on
                all_postings[key]['last_collected_on'] = collected_on
            else:
                if not extend:
                    for col, row in value.items():
                        if (col not in all_postings[key].keys()) or (not all_postings[key][col]):
                            all_postings[key][col] = row       
                    if collected_on:
                        stored_first_collected_on = all_postings[key]['first_collected_on']
                        stored_last_collected_on = all_postings[key]['last_collected_on']
                        if not stored_last_collected_on or collected_on > stored_last_collected_on:
                            all_postings[key]['last_collected_on'] = collected_on
                            #update text to latest version
                            all_postings[key]["description"] = value.get("description", all_postings[key].get("description",None)) 
                        if not stored_first_collected_on or collected_on < stored_first_collected_on:
                            all_postings[key]['first_collected_on'] = collected_on
                else:#extend==True
                    if not isinstance(all_postings[key], list):
                        all_postings[key] = [all_postings[key]]
                    value['first_collected_on'] = collected_on or all_postings[key][0]['first_collected_on']
                    value['last_collected_on'] = collected_on or all_postings[key][0]['last_collected_on']
                    all_postings[key].append(value)
                    if collected_on:
                        stored_first_collected_on = all_postings[key][0]['first_collected_on']
                        stored_last_collected_on = all_postings[key][0]['last_collected_on']
                        if (not stored_first_collected_on or collected_on > stored_first_collected_on):
                            for posting_store in all_postings[key]:
                                posting_store['last_collected_on'] = collected_on
                                posting_store["description"] = value.get("description", posting_store.get("description",None))
                        if (not stored_last_collected_on or collected_on < stored_last_collected_on):
                            for posting_store in all_postings[key]:
                                posting_store['first_collected_on'] = collected_on
    return all_postings

def enrich_postings(postings:str|dict, filename=None, overwrite=True, keywords = BASE_KEYWORDS, extra_keywords = {}, **kwargs):
    from methods.sites import BaseScraper
    if isinstance(postings, str):
        filename = filename or postings

    postings = load_file_if_str(postings, type_="dict")
    scraper = BaseScraper(driver="skip", keywords=keywords, extra_keywords=extra_keywords)
    for posting_id, posting in postings.copy().items():
        if 'salary' in posting.keys():
            salary_read = scraper.salary_from_text(posting['salary'])
        else:
            salary_read = scraper.salary_from_description(posting.get("description",[]), **kwargs)
        if overwrite or ('salary_guessed' not in posting.keys()) or (not posting['salary_guessed']):
            posting['salary_guessed'] = salary_read
        if overwrite or ('salary_monthly_guessed' not in posting.keys()) or (not posting['salary_monthly_guessed']):
            posting['salary_monthly_guessed'] = salary_read["monthly"] if salary_read else None

        if 'collected_on' not in posting.keys() or (not posting['collected_on']): #don't overwrite
            posting['collected_on'] = get_date_of_collection(value=posting, filename=filename, overwrite=False)
        
    postings = scraper.find_keywords_in_postings(postings, sort=False, overwrite=overwrite, **kwargs)
    postings = scraper.rank_postings(postings, overwrite=overwrite, **kwargs)
    return postings
