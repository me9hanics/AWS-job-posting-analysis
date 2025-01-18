import json
import os
import time

def compare_lists(new, previous, print_out=True):
    """
    Compare two lists and return the differences.
    If new or previous is a string, the list is read from a file.
    """
    if isinstance(new, str):
        with open(new, 'r', encoding="utf-8") as f:
            new = json.load(f)
    if isinstance(previous, str):
        with open(previous, 'r', encoding="utf-8") as f:
            previous = json.load(f) 
    added = list(set(new) - set(previous))
    removed = list(set(previous) - set(new))
    if print_out:
        print("New items: ", added)
        print("Removed items: ", removed)
    return added, removed

def save_list(list_, filename):
    with open(filename, 'w', encoding="utf-8") as f:
        json.dump(list_, f, indent=4, ensure_ascii=False)

def save_data(data, path = "source/save/postings/", name="", with_date = True, verbose = False):
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