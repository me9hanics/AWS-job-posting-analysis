import sys
import os
schedule_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.join(schedule_path, "..")
sys.path.append(parent_path)
try:
    from datacollect import get_postings
except:
    from .datacollect import get_postings
from methods.sites import SALARY_BEARABLE, BASE_KEYWORDS, BASE_RANKINGS

def get_tech_postings(keywords=BASE_KEYWORDS, rankings=BASE_RANKINGS, salary_bearable=SALARY_BEARABLE,
                      prefix ="postings", path="C:/GitHubRepo/AWS-job-posting-analysis/source/save/postings/tech/",
                      path_excel="C:/GitHubRepo/AWS-job-posting-analysis/source/save/excels/excel_tech/",
                      **kwargs):
    """
    Collect legal job postings from various websites.
    
    Parameters:
    keywords (dict): Keywords for filtering job postings.
    rankings (dict): Rankings for scoring job postings.
    salary_bearable (int): Minimum salary to consider a job posting bearable.
    
    Returns:
    dict: A dictionary containing the results, added and removed postings, and companies.
    """
    kwargs['raiffeisen_extra_titlewords'] = kwargs.get('raiffeisen_extra_titlewords', ["machine", "engineer", "scientist"])
    data = get_postings(
        keywords=keywords, 
        rankings=rankings, 
        salary_bearable=salary_bearable,
        prefix=prefix,
        path=path,
        path_excel=path_excel
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
        keywords=BASE_KEYWORDS, 
        rankings=BASE_RANKINGS,
        salary_bearable=SALARY_BEARABLE,
    )
    results = data["results"]
    print(f"Found {len(results)} postings in total")
    added = [instance["title"] + " - at - " + instance["company"] for key, instance in data["added"].items() if "title" in instance]
    removed = [instance["title"] + " - at - " + instance["company"] for key, instance in data["removed"].items() if "title" in instance]
    print(f"\nAdded postings:\n")
    for title in added:
        print(title)
    #print(f"\nRemoved postings:\n")
    #for title in removed:
    #    print(title)
    companies = data["companies"]

if __name__ == "__main__":
    main()