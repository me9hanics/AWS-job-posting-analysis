import json
import os
import time

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

def save_data(data, path = "source/save/postings/", name="", with_date = True, verbose = False):
    """
    Save data to a JSON file, optionally with a date in the name.
    
    Parameters:
    data (dict | list | str): The data to save.
    path (str): The directory path to save the file to.
    name (str): The name of the file, without the date extension.
    with_date (bool): Whether to include the date in the name.
    verbose (bool): Whether to print a message if the data type is not supported.

    Returns:
    None
    """
    if not os.path.exists(path):
        os.makedirs(path)
    if not name:
        name = "postings"
    if with_date:
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

def load_list_items(files=None, folder_path = "source/save/postings/", type_ = "dict"):
    """
    Load a list of files, optionally from a directory path.
    
    Parameters:
    files (list): The list of file names to load.
    path (str): The directory path to load the files from.
    type (str): The type of the data to load, either "dict" or "list".

    Returns:
    files (list): The list of loaded files.
    """
    if folder_path[-1] != "/":
        folder_path += "/"
    if not isinstance(files, list): #e.g. string
        files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    contents = []
    for i, file in enumerate(files):
        if isinstance(file, str):
            contents.append(load_file_if_str(f"{folder_path}{file}", type_))
    return contents

def load_file_from_dir(path = "source/save/postings/", prefix = "postings", ascending = True,
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
        return files[index]
    else:
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

def compare_lists(new, previous, print_out="complete_lists", printed_text_max_length = None):
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
    added = sort_dict_by_key(added, key="points", descending = True)
    removed = {key: previous[key] for key in removed_keys}
    removed = sort_dict_by_key(removed, key="points", descending = True)

    if print_out=="complete_lists":
        #make print out a list of all of the keys in the dictionaries, every single key that appears at least once
        print_out = list(
                    get_nested_dict_keys(new, appear="any", return_type=set).union(
                    get_nested_dict_keys(previous, appear="any", return_type=set))
                    )
    elif print_out=="only_lengths":
        print("Amount of new items: ", len(added_keys))
        print("Amount of removed items: ", len(removed_keys))
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
        print("New items: ")
        for posting_key in print_added:
            text = ",\n\t".join([str(u)+": "+str(v) for u,v in (print_added[posting_key].items()) if u in print_out])     
            print(f"\n{posting_key}: \n\t{text}")
        print("\n\n\nRemoved items: ")
        for posting_key in print_removed:
            text = ",\n\t".join([str(u)+": "+str(v) for u,v in (print_removed[posting_key].items()) if u in print_out])
            print(f"\n{posting_key}: \n\t{text}")

    return added, removed

def compare_postings(new, previous, print_attrs=["title", "company", "points"], printed_text_max_length = 100):
    """
    Compare two lists of postings and return the differences.
    If new or previous is a string, the list is read from a file.

    Parameters:
    new (list | str): The new list of postings, optionally read from a file.
    previous (list | str): The previous list of postings, optionally read from a file.
    print_out_titles (bool): Whether to print out the titles of the postings.

    Returns:
    added (dict): The new postings that were added.
    removed (dict): The old postings that were removed.
    """

    print_out = print_attrs if print_attrs else "none"
    return compare_lists(new, previous, print_out, printed_text_max_length)

def combine_postings(postings=None, folder_path="source/save/postings/asd/", extend = False):
    """
    Combine multiple lists of postings into one list.
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
            if key not in all_postings:
                all_postings[key] = value
            elif extend == True:
                if not isinstance(all_postings[key], list):
                    all_postings[key] = [all_postings[key]]
                all_postings[key].extend(value)
    return all_postings