"""File and folder helpers for loading and saving postings data."""

import json
import os
import time
from datetime import datetime
from jobscraping.config.configs import RELATIVE_POSTINGS_PATH
from typing import Any

def save_list(list_: list, filename: str) -> None:
    """
    Save a list to a JSON file.

    Parameters:
    list_ (list): The list to save.
    filename (str): The name of the file to save the list to.

    Returns:
    None
    """
    with open(filename, "w", encoding="utf-8") as file_obj:
        json.dump(list_, file_obj, indent=4, ensure_ascii=False)

def save_data(
    data: dict | list | str,
    path: str = f"{RELATIVE_POSTINGS_PATH}/",
    name: str = "",
    with_timestamp: bool = True,
    verbose: bool = False,
) -> None:
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
    with open(f"{path}{name}", "w", encoding="utf-8") as file_obj:
        if type(data) in [dict, list, str]:
            json.dump(data, file_obj, indent=4, ensure_ascii=False)
        else:
            if verbose:
                print(f"Could not save data of type {type(data)}")

def load_file_if_str(file: str | Any, type_: str = "dict") -> object:
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
        with open(file, "r", encoding="utf-8") as file_obj:
            if type_ == "dict":
                file = json.load(file_obj)
            elif type_ == "list":
                file = file_obj.read().splitlines()
    return file

def explore_nested_folder(folder_path: str = f"{RELATIVE_POSTINGS_PATH}/") -> list[str]:
    """Return all JSON files under a folder, exploring nested directories."""
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

def filter_files_by_date(
    files: list[str],
    min_date: str | datetime | None = None,
) -> list[str]:
    """
    Select files created after a specific date only.
    Warning: On Linux, the creation date may not be correct.
    """
    if not min_date:
        return files
    if isinstance(min_date, str):
        min_date = datetime.strptime(min_date, "%Y.%m.%d")
    filtered = []
    for file_path in files:
        #getctime: creation time (Windows), but metadata change time (Unix)
        #https://stackoverflow.com/a/39501288/19626271
        creation_date = datetime.fromtimestamp(os.path.getctime(file_path))
        if creation_date >= min_date:
            filtered.append(file_path)
    return filtered

def get_files(
    files: str | list[str] | None = None,
    folder_path: str = f"{RELATIVE_POSTINGS_PATH}/",
    nested: bool = False,
) -> list[str]:
    """Resolve files list against a folder path, optionally exploring nested folders."""
    if isinstance(files, str):
        files = [files]
    if folder_path:
        if folder_path[-1] != "/":
            folder_path += "/"

        if not isinstance(files, list):
            if nested:
                files = explore_nested_folder(folder_path)
            else:
                files = [
                    folder_path + file_name
                    for file_name in os.listdir(folder_path)
                    if file_name.endswith(".json")
                ]
        else:
            files = [
                folder_path + file_path if not file_path.startswith(folder_path) else file_path
                for file_path in files
            ]
    return files

def load_list_items(
    files: str | list[str] | None = None,
    folder_path: str = f"{RELATIVE_POSTINGS_PATH}/",
    type_: str = "dict",
    nested: bool = False,
) -> list:
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
    for file_path in files:
        if isinstance(file_path, str):
            contents.append(load_file_if_str(file_path, type_))
    return contents

def get_filename_from_dir(
    path: str = f"{RELATIVE_POSTINGS_PATH}/",
    prefix: str = "postings",
    ascending: bool = True,
    ending: str = ".json",
    index: int = 0,
) -> str | None:
    """
    Load the last file in a directory, optionally with a prefix.
    
    Parameters:
    path (str): The directory path to load the file from.
    prefix (str): The prefix of the file name.
    ascending (bool): Whether to sort the files in ascending order.

    Returns:
    file (str): The name of the last file in the directory.
    """
    
    files = [
        file_name
        for file_name in os.listdir(path)
        if file_name.startswith(prefix) and file_name.endswith(ending)
    ]
    files.sort(reverse = not ascending)
    if files:
        #check if index is within the range of files
        if -len(files) <= index < len(files):
            return files[index]
    return None
