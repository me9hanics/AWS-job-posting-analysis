import json

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