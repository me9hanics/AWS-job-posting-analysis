#Scrape website
import datetime
import pandas as pd
import time
from typing import List, Type

import sys
import os
schedule_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.join(schedule_path, "..")
sys.path.append(parent_path)
from methods import files_io, postings_utils, datastruct_utils, sites, configs #constants
from methods.constants import *
from methods.configs import *

KEYWORDS = configs.BASE_PHRASES.copy()
RANKINGS = configs.BASE_KEYWORD_SCORING.copy()
SCRAPERS = [sites.KarriereAT, sites.Raiffeisen]
SALARY_BEARABLE = configs.SALARY_BEARABLE

def ensure_output_paths(path, current_postings_filename, newly_added_postings_filename,
                        postings_history_filename):
    """Ensure posting output paths exist."""
    if path:
        if not path.endswith("/"):
            path = f"{path}/"
        os.makedirs(path, exist_ok=True)
        for filename in [current_postings_filename, newly_added_postings_filename, postings_history_filename]:
            if filename:
                file_path = f"{path}{filename}"
                if not os.path.exists(file_path):
                    files_io.save_data({}, path=path, name=filename, with_timestamp=False)


    return path

def reorder_locations(locations, primary = LOCATIONS_DESIRED):
    """Reorder locations: have primary first, then the rest."""
    if not isinstance(locations, list) or not locations:
        return locations
    first_locs = []
    other_locs = []
    for loc in locations:
        if isinstance(loc, str) and any(city in loc.lower() for city in primary):
            first_locs.append(loc)
        else:
            other_locs.append(loc)
    return first_locs + other_locs

def scrape_sites(scrapers: List[Type[sites.BaseScraper]] = SCRAPERS, keywords=KEYWORDS, rankings=RANKINGS, salary_bearable=SALARY_BEARABLE,
                 verbose=False, verbose_data_gathering=False, **kwargs):
    results = {}
    for scraper_class in scrapers:
        scraper = scraper_class(keywords=keywords, rankings=rankings, salary_bearable=salary_bearable,
                                extra_keywords=kwargs.get(f"{scraper_class.__name__.lower()}_extra_keywords", kwargs.get("extra_keywords", {})),
                                extra_titlewords=kwargs.get(f"{scraper_class.__name__.lower()}_extra_titlewords", kwargs.get("extra_titlewords", [])),
                                extra_locations=kwargs.get(f"{scraper_class.__name__.lower()}_extra_locations", kwargs.get("extra_locations", [])),
                                locations_secondary=kwargs.get(f"{scraper_class.__name__.lower()}_locations_secondary", kwargs.get("locations_secondary", LOCATIONS_SECONDARY)),
                                rules=kwargs.get(f"{scraper_class.__name__.lower()}_rules", kwargs.get("rules", BASE_RULES)),
                                transformations = kwargs.get(f"{scraper_class.__name__.lower()}_transformations", kwargs.get("transformations", [])),
                                )
        scrape_start = time.time()
        run_results = scraper.gather_data(descriptions=True, verbose=verbose_data_gathering)
        scrape_elapsed = time.time() - scrape_start
        if verbose:
            print(f"Found {len(run_results)} postings on {scraper_class.__name__} in {scrape_elapsed:.2f}s")
        results = {**results, **run_results}
    return results

def get_postings(scrapers = SCRAPERS, keywords =KEYWORDS, rankings=RANKINGS, salary_bearable=SALARY_BEARABLE,
                 path=f"{RELATIVE_POSTINGS_PATH}/", verbose=False, verbose_data_gathering=False, threshold = 0.01,
                 col_order = COLUMN_ORDER, efficient_storing = True, only_thresholded_stored = False,
                 current_postings_filename = CURRENT_POSTINGS_FILENAME,
                 newly_added_postings_filename = NEWLY_ADDED_POSTINGS_FILENAME,
                 postings_history_filename = POSTINGS_HISTORY_FILENAME, **kwargs):
    path= ensure_output_paths(
        path,
        current_postings_filename,
        newly_added_postings_filename,
        postings_history_filename,
    )
    keywords['titlewords'] = list(set(keywords['titlewords']))
    results = scrape_sites(scrapers = scrapers, keywords=keywords, rankings=rankings, salary_bearable=salary_bearable,
                            verbose=verbose, verbose_data_gathering=verbose_data_gathering, **kwargs)
    results = datastruct_utils.reorder_dict(results, col_order, nested=True)
    results = {k: v for k, v in sorted(results.items(), key=lambda item: item[1]["points"], reverse=True)}
    if verbose:
        print(f"Found {len(results)} results in total")
    
    previous_file_name = "postings_history.json"
    if not os.path.exists(f"{path}{previous_file_name}"):
        previous_file_name = files_io.get_filename_from_dir(path, index = -1) #if there is no file, returns None
    added, removed = postings_utils.get_added_and_removed(results, f'{path}{previous_file_name}' if previous_file_name else [])

    if only_thresholded_stored:
        added = postings_utils.threshold_postings_by_points(added, points_threshold=threshold)
        removed = postings_utils.threshold_postings_by_points(removed, points_threshold=threshold)
        results = postings_utils.threshold_postings_by_points(results, points_threshold=threshold)

    files_io.save_data(results, path=path, name=current_postings_filename, with_timestamp=False, )

    if not efficient_storing or not previous_file_name:
        files_io.save_data(results, name=postings_history_filename if efficient_storing else "",
                           path=path, with_timestamp=False if efficient_storing else True)
    else: #efficient storing
        history = postings_utils.unify_postings(folder_path=path) #includes newly_added_postings
        for key in history.keys():
            try:
                dt_last = datetime.datetime.strptime(history[key].get('last_collected_on', ""), "%Y-%m-%d")
                dt_first = datetime.datetime.strptime(history[key].get('first_collected_on', ""), "%Y-%m-%d")
            except ValueError:
                continue
            history[key]['timespan_days'] = (dt_last - dt_first).days
        for key in results.keys() & history.keys():
            results[key]['first_collected_on'] = history[key]['first_collected_on']
            results[key]['last_collected_on'] = history[key]['last_collected_on']
            if 'timespan_days' in history[key]:
                results[key]['timespan_days'] = history[key]['timespan_days']
        for key in added.keys() & history.keys():
            added[key]['first_collected_on'] = history[key]['first_collected_on']
            added[key]['last_collected_on'] = history[key]['last_collected_on']
            if 'timespan_days' in history[key]:
                added[key]['timespan_days'] = history[key]['timespan_days']

        files_io.save_data(history, path=path, name=postings_history_filename, with_timestamp=False)
        #Re-run: adding first and last collected on to results
        files_io.save_data(results, path=path, name=current_postings_filename, with_timestamp=False)

    files_io.save_data(added, path=path, name=newly_added_postings_filename, with_timestamp=False, )

    if threshold is not None:
        added = postings_utils.threshold_postings_by_points(added, points_threshold=threshold)
        removed = postings_utils.threshold_postings_by_points(removed, points_threshold=threshold)
        results = postings_utils.threshold_postings_by_points(results, points_threshold=threshold)
    if verbose:
        print(f"Found {len(results)} postings. Added {len(added)} postings, removed {len(removed)} postings." + " above threshold" if threshold is not None else "")

    df = pd.DataFrame.from_dict(results, orient='index')
    df["locations"] = df["locations"].apply(lambda x: x if isinstance(x, list) else [])
    df["locations"] = df["locations"].apply(reorder_locations, primary=kwargs.get("locations_primary", LOCATIONS_DESIRED))
    companies = list(df[df['locations'].apply(lambda locs: any("wien" in loc.lower() or "vienna" in loc.lower() for loc in locs))]['company'].unique())

    excel_file_path = None

    output_dict = {
        "results": results,
        "added": added, #above threshold
        "removed": removed, #above threshold
        "companies": companies,
        "excel_file_path": excel_file_path,
    }
    return output_dict

if __name__ == "__main__":
    data = get_postings()
    print("Found:" , len(data["results"]), "postings")
    #print(data) #find a nice format
