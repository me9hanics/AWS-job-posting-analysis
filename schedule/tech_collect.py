import sys
import os
schedule_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.join(schedule_path, "..")
sys.path.append(parent_path)
try:
    from datacollect import get_postings
except:
    from .datacollect import get_postings
from methods.constants import *

def get_tech_postings(keywords=BASE_PHRASES, rankings=BASE_KEYWORD_SCORING, salary_bearable=SALARY_BEARABLE,
                      path=f"{POSTINGS_PATH}/tech/", path_excel=f"{EXCELS_PATH}/excel_tech/",
                      excel_prefix ="postings", **kwargs):
    """
    Collect legal job postings from various websites.
    
    Parameters:
    keywords (dict): Keywords for filtering job postings.
    rankings (dict): Rankings for scoring job postings.
    salary_bearable (int): Minimum salary to consider a job posting bearable.
    
    Returns:
    dict: A dictionary containing the results, added and removed postings, and companies.
    """
    kwargs['raiffeisen_extra_titlewords'] = kwargs.get('raiffeisen_extra_titlewords', ["machine", "engineer", "developer", "scientist", "quantitative"])
    data = get_postings(
        keywords=keywords, 
        rankings=rankings, 
        salary_bearable=salary_bearable,
        prefix=excel_prefix,
        path=path,
        path_excel=path_excel,
        **kwargs
    )
    #results = data["results"]
    #added = data["added"]
    #removed = data["removed"]
    #companies = data["companies"]
    return data

def main():
    print("Collecting tech job postings...")
    data = get_tech_postings(
        keywords=BASE_PHRASES, 
        rankings=BASE_KEYWORD_SCORING,
        salary_bearable=SALARY_BEARABLE,
        verbose=True,
    )
    results = data["results"]
    print(f"\nFound {len(results)} postings above threshold.")
    added = [instance["title"] + " - at - " + instance["company"] for key, instance in data["added"].items() if "title" in instance]
    removed = [instance["title"] + " - at - " + instance["company"] for key, instance in data["removed"].items() if "title" in instance]
    keyword_counts = {keyword: sum(keyword in instance["keywords"]
                                   for instance in results.values()) for keyword in MAIN_DESCRIPTION_KEYWORDS}
    print(f"\nKeywords in number of descriptions:\n")
    for keyword, count in keyword_counts.items():
        print(f"{keyword}: {count}")
    print(f"\nNew postings above threshold:\n")
    for title in added:
        print(title)
    #print(f"\nRemoved postings:\n")
    #for title in removed:
    #    print(title)
    return data

if __name__ == "__main__":
    main()