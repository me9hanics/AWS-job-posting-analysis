import re

# ============================================================================
# DATA STORAGE CONSTANTS
# ============================================================================
# These constants define file paths and naming conventions for storing job postings data

COLUMN_ORDER = ["title", "company",  "salary_monthly_guessed",
                "locations", "keywords",
                "points", "url", "language",
                "snippet", "description", "salary",
                "employmentTypes", "salary_guessed",
                "collected_on", "date", "id", "isHomeOffice", "isActive", "source"]
EXCEL_COLUMNS = {
    'title': {'as': 'Title', 'column': 'A', 'width': 38},
    'company': {'as': 'Company', 'column': 'B', 'width': 24},
    'salary_monthly_guessed': {'as': 'Salary?', 'column': 'C', 'width': 6.56},
    'locations': {'as': 'Locations', 'column': 'D', 'width': 14.33},
    'keywords': {'as': 'Keywords', 'column': 'E', 'width': 50.44},
    'url': {'as': 'URL', 'column': 'F', 'width': 20.44},
    'isHomeOffice': {'as': 'HomeOffice', 'column': 'G', 'width': 6},
    'points': {'as': 'Points', 'column': 'H', 'width': 6},
    'first_collected_on': {'as': 'First date', 'column': 'I', 'width': 12},
    'description': {'as': 'Description', 'column': 'J', 'width': 114}
}
CURRENT_POSTINGS_FILENAME = "current_postings.json"
NEWLY_ADDED_POSTINGS_FILENAME = "newly_added_postings.json"
POSTINGS_HISTORY_FILENAME = "postings_history.json"

# ============================================================================
# WEBSITE-SPECIFIC SCRAPING CONFIGURATION
# ============================================================================
# These rules define how to scrape each website. Vary per site.

BASE_RULES = {"website": "",
              "scraping_base_url": "",
              "close_website_popup": False,
              "usecase": 'http',
              "gather_data_selector": "",
              "load_page_button_selector": "",
              "request_wait_time": 0.15,
              "title_path": None,
              "company_path": None,
              "salary_path": None,
              }

KARRIEREAT_RULES = {
    "website": "karriere.at",
    "scraping_base_url": "https://www.karriere.at/jobs",
    "close_website_popup": False,
    "usecase": "https",
    "gather_data_selector": 'div.m-jobsListItem__container div.m-jobsListItem__dataContainer h2.m-jobsListItem__title a.m-jobsListItem__titleLink',
    "load_page_button_selector": ".onetrust-close-btn-handler",
    "load_page_press_button_until_gone_selector": ".m-loadMoreJobsButton__button",
    "request_wait_time": 0.16,
    "title_path": None,
    "company_path": None,
    "salary_path": None,
}

RAIFFEISEN_RULES = {
    "website": "raiffeisen_international",
    "scraping_base_url": "https://jobs.rbinternational.com/search/?q=",
    "jobs_base_url": "https://jobs.rbinternational.com",
    "usecase": "http",
    "gather_data_selector": "a.jobTitle-link",
    "more_pages_url_extension": "&sortColumn=referencedate&sortDirection=desc&startrow=",
    "description_selector": "ul",
    "request_wait_time": 0.3,
    "title_path": None,
    "company_path": None,
    "salary_path": None,
    "close_website_popup": False,
    "load_page_button_selector": "",
}
