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
                      prefix ="postings", path="C:/GitHubRepo/AWS-job-posting-analysis/source/save/postings/",
                      path_excel="C:/GitHubRepo/AWS-job-posting-analysis/source/save/excels/"):
    """
    Collect legal job postings from various websites.
    
    Parameters:
    keywords (dict): Keywords for filtering job postings.
    rankings (dict): Rankings for scoring job postings.
    salary_bearable (int): Minimum salary to consider a job posting bearable.
    
    Returns:
    dict: A dictionary containing the results, added and removed postings, and companies.
    """
    data = get_postings(
        keywords=keywords, 
        rankings=rankings, 
        salary_bearable=salary_bearable,
        prefix=prefix,
        path=path,
        path_excel=path_excel
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
    added = [instance["title"] for instance in data["added"] if "title" in instance]
    removed = [instance["title"] for instance in data["removed"] if "title" in instance]
    print(f"Added postings: {(added)}")
    print(f"Removed postings: {(removed)}")
    companies = data["companies"]

if __name__ == "__main__":
    main()