import json
import os
import time
from datetime import datetime
from typing import List, Dict
from methods.macros import *

def save_list(list_, filename):
    """
    Save a list to a JSON file.

    Parameters:
    list_ (list): The list to save.
    filename (str): The name of the file to save the list to.

    Returns:
    None
    """
    with open(filename, 'w', encoding="utf-8") as f:
        json.dump(list_, f, indent=4, ensure_ascii=False)

def save_data(data, path = f"{RELATIVE_POSTINGS_PATH}/", name="", with_timestamp = True, verbose = False):
    """
    Save data to a JSON file, optionally with a date in the name.
    
    Parameters:
    data (dict | list | str): The data to save.
    path (str): The directory path to save the file to.
    name (str): The name of the file, without the date extension.
    with_timestamp (bool): Whether to include the date in the name.
    verbose (bool): Whether to print a message if the data type is not supported.

    Returns:
    None
    """
    if not os.path.exists(path):
        os.makedirs(path)
    if not name:
        name = "postings"
    if with_timestamp:
        date = time.strftime("%Y-%m-%d-%H-%M-%S")
        name = f"{name}_{date}"
    with open(f"{path}{name}.json", "w", encoding="utf-8") as file:
        if type(data) in [dict, list, str]:
            json.dump(data, file, indent=4, ensure_ascii=False)
        else:
            if verbose:
                print(f"Could not save data of type {type(data)}")

def load_file_if_str(file, type_ = "dict"):
    """
    Load a file if the input is a string, otherwise return the input.
    (Convenience abstraction.)

    Parameters:
    file (any): The file or data to load.
    type (str): The type of the data to load, either "dict" or "list".

    Returns:
    file (any): The loaded file; possibly the original data.
    """
    if isinstance(file, str):
        with open(file, 'r', encoding="utf-8") as f:
            if type_ == "dict":
                file = json.load(f)
            elif type_ == "list":
                file = f.read().splitlines()
    return file

def explore_nested_folder(folder_path = f"{RELATIVE_POSTINGS_PATH}/"):
    if not isinstance(folder_path, str):
        return []
    if folder_path[-1] != "/":
        folder_path += "/"
    files = []
    for root, _, filenames in os.walk(folder_path):
        if not root.endswith("/"):
            root += "/"
        for filename in filenames:
            if filename.endswith(".json"):
                files.append(root + filename)
    return files

def filter_files_by_date(files, min_date=None):
    """
    Select files created after a specific date only.
    Warning: On Linux, the creation date may not be correct.
    """
    if not min_date:
        return files
    if isinstance(min_date, str):
        min_date = datetime.strptime(min_date, "%Y.%m.%d")
    filtered = []
    for f in files:
        #getctime: creation time (Windows), but metadata change time (Unix)
        #https://stackoverflow.com/a/39501288/19626271
        creation_date = datetime.fromtimestamp(os.path.getctime(f))
        if creation_date >= min_date:
            filtered.append(f)
    return filtered

def get_files(files=None, folder_path = f"{RELATIVE_POSTINGS_PATH}/", nested = False):
    if isinstance(files, str):
        files = [files]
    if folder_path:
        if folder_path[-1] != "/":
            folder_path += "/"

        if not isinstance(files, list):
            if nested:
                files = explore_nested_folder(folder_path)
            else:
                files = [folder_path + f for f in os.listdir(folder_path) if f.endswith(".json")]
        else:
            files = [folder_path + f if not f.startswith(folder_path) else f for f in files]
    return files

def load_list_items(files=None, folder_path = f"{RELATIVE_POSTINGS_PATH}/",
                    type_ = "dict", nested = False):
    """
    Load a list of files, optionally from a directory path.
    
    Parameters:
    files (list): The list of file names to load.
    path (str): The directory path to load the files from.
    type (str): The type of the data to load, either "dict" or "list".

    If there is no folder path given, the current directory is used.
    If there is a folder path given, but no files, all JSON files in the folder are loaded.
        Optionally, nested folders are explored.
    If there is a folder path and a list of files, the files are loaded from the folder path.

    Returns:
    files (list): The list of loaded files.
    """
    files = get_files(files, folder_path, nested)
    contents = []
    for i, file in enumerate(files):
        if isinstance(file, str):
            contents.append(load_file_if_str(file, type_))
    return contents

def get_filename_from_dir(path = f"{RELATIVE_POSTINGS_PATH}/", prefix = "postings", ascending = True,
                       ending = ".json", index = 0):
    """
    Load the last file in a directory, optionally with a prefix.
    
    Parameters:
    path (str): The directory path to load the file from.
    prefix (str): The prefix of the file name.
    ascending (bool): Whether to sort the files in ascending order.

    Returns:
    file (str): The name of the last file in the directory.
    """
    
    files = [f for f in os.listdir(path) if f.startswith(prefix) and f.endswith(ending)]
    files.sort(reverse = not ascending)
    if files:
        #check if index is within the range of files
        if index < len(files) and index >= -len(files): 
            return files[index]
    return None

def sort_dict_by_key(x, key="points", descending = True):
    return {k: v for k, v in sorted(x.items(), key=lambda item: item[1][key], reverse = descending)} if x else {}

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

def compare_postings(new = None, previous = None, print_attrs=["title", "company", "points"], printed_text_max_length = 100,
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
                                all_postings[key]["description"] = value.get("description", all_postings[key]["description"]) #update text to latest version
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
                                posting_store["description"] = value.get("description", posting_store["description"]) #update text to latest version
                        if (not stored_last_collected_on or collected_on < stored_last_collected_on):
                            for posting_store in all_postings[key]:
                                posting_store['first_collected_on'] = collected_on
    return all_postings

def reorder_dict(d, keys_order, nested=False):
    return {k: d[k] for k in keys_order if k in d} if not nested else {
        k: reorder_dict(d[k], keys_order, nested=False) for k in d.keys()
    }
