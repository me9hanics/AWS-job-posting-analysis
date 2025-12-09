from methods.macros import *
from methods.files_io import load_file_if_str, load_list_items
import re
import os
from datetime import datetime
from typing import List, Dict
from methods.datastruct_utils import sort_dict_by_key, get_nested_dict_keys
from methods.attributes import salary_from_text

def filter_postings(postings:dict, banned_words=None, banned_capital_words=None):
    filtered_postings = {}
    for id, posting in postings.items():
        title = posting["title"]
        if any([word in title.lower() for word in banned_words]):
            continue
        if any([word in title for word in banned_capital_words]):
            continue
        filtered_postings[id] = posting
    return filtered_postings

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
    
    for posting in new.values():
        if 'points' not in posting or posting['points'] is None:
            posting['points'] = 0
    for posting in previous.values():
        if 'points' not in posting or posting['points'] is None:
            posting['points'] = 0
    
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
                    #Update missing fields
                    for col, row in value.items():
                        if (col not in all_postings[key].keys()) or (not all_postings[key][col]):
                            all_postings[key][col] = row
                    
                    stored_first = all_postings[key].get('first_collected_on')
                    if first_collected:
                        if not stored_first or first_collected < stored_first:
                            all_postings[key]['first_collected_on'] = first_collected
                    
                    stored_last = all_postings[key].get('last_collected_on')
                    if last_collected:
                        if not stored_last or last_collected > stored_last:
                            all_postings[key]['last_collected_on'] = last_collected
                            #Update description to latest version
                            all_postings[key]["description"] = value.get("description", all_postings[key].get("description", None))
                    
                else:  # extend==True
                    if not isinstance(all_postings[key], list):
                        all_postings[key] = [all_postings[key]]
                    value['first_collected_on'] = first_collected or all_postings[key][0].get('first_collected_on')
                    value['last_collected_on'] = last_collected or all_postings[key][0].get('last_collected_on')
                    all_postings[key].append(value)
                    
                    # Update global min/max across all versions
                    if first_collected or last_collected:
                        global_first = min((v.get('first_collected_on') for v in all_postings[key] if v.get('first_collected_on')), default=None)
                        global_last = max((v.get('last_collected_on') for v in all_postings[key] if v.get('last_collected_on')), default=None)
                        
                        for posting_store in all_postings[key]:
                            posting_store['first_collected_on'] = global_first
                            posting_store['last_collected_on'] = global_last
                            if posting_store.get('last_collected_on') == global_last:
                                posting_store["description"] = value.get("description", posting_store.get("description", None))
    
    return all_postings

def enrich_postings(postings:str|dict, filename=None, overwrite=True, keywords = BASE_KEYWORDS, 
                    extra_keywords = {}, **kwargs): #rankings = BASE_KEYWORD_SCORING, 
    from methods.sites import BaseScraper
    if isinstance(postings, str):
        filename = filename or postings

    postings = load_file_if_str(postings, type_="dict")
    scraper = BaseScraper(driver="skip", keywords=keywords, extra_keywords=extra_keywords)
    for posting_id, posting in postings.copy().items():
        if 'salary' in posting.keys():
            salary_read = scraper._salary_from_text(posting['salary'])
        else:
            salary_read = scraper._salary_from_description(posting.get("description",[]), **kwargs)
        if overwrite or ('salary_guessed' not in posting.keys()) or (not posting['salary_guessed']):
            posting['salary_guessed'] = salary_read
        if overwrite or ('salary_monthly_guessed' not in posting.keys()) or (not posting['salary_monthly_guessed']):
            posting['salary_monthly_guessed'] = salary_read["monthly"] if salary_read else None

        if 'collected_on' not in posting.keys() or (not posting['collected_on']): #don't overwrite
            posting['collected_on'] = get_date_of_collection(value=posting, filename=filename, overwrite=False)
        
    postings = scraper._find_keywords_in_postings(postings, sort=False, overwrite=overwrite, **kwargs)
    postings = scraper._rank_postings(postings, overwrite=overwrite, **kwargs)
    return postings

def process_posting_soups(soups, pattern, website = "",
                  posting_id=False, posting_id_path=None,
                  posting_id_regex=r'\d+', title_path=None, 
                   company_path=None, salary_path=None):
    postings = {}
    for soup in soups:
        selects = soup.select(pattern)
        for select in selects:
            id = None
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
                    id = re.search(posting_id_regex, select.text).group()
                else:
                    id = re.search(posting_id_regex, select[posting_id_path]).group()
                if (id is not None) and (id in postings.keys()):
                    _text = select.text
                    if _text:
                        _text = _text.strip()
                    postings[id] = {"title": title, "company": company, "id":id,
                                    "source": website, "salary": salary,
                                    "salary_versions": salary_versions, "text": _text}
            else:
                _text = select.text
                if _text:
                    _text = _text.strip()
                if _text and (_text not in postings.keys()):
                    postings[_text] = {"title": title, "company": company, "id":None,
                                       "source": website, "salary": salary,
                                       "salary_versions": salary_versions, "text": _text}
    return postings