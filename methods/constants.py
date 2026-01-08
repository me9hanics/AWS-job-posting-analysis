import re

# ============================================================================
# WEBSITE-SPECIFIC SCRAPING CONFIGURATION
# ============================================================================
# These rules define how to scrape each website and vary per site

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