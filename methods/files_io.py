import json
import os
import time
from datetime import datetime
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
    if not name.endswith(".json"):
        name += ".json"
    with open(f"{path}{name}", "w", encoding="utf-8") as file:
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
