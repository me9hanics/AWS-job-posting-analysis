import requests
from bs4 import BeautifulSoup
import re
import time
import json
import os
try:
    from methods import scrape
    from methods import urls
except ModuleNotFoundError:
    import scrape
    import urls

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, TimeoutException

GET_HEIGHT_SCRIPT = "return document.body.scrollHeight"
SCROLL_DOWN_SCRIPT = "window.scrollTo(0, document.body.scrollHeight);" #scroll to height value of the bottom of the page
SCROLL_1000_SCRIPT = "window.scrollTo(0, 1000);"
CSS_SELECTOR = "css selector" #can use instead: from selenium.webdriver.common.by import By, then By.CSS_SELECTOR

SALARY_BEARABLE = 3400

BASE_RULES = {"website":"karriere.at",
              "scraping_base_url": "https://www.karriere.at/jobs",
              "close_website_popup":False,
              "usecase":'http',
              "load_page_button_selector":".onetrust-close-btn-handler",
              "load_page_press_button_until_gone_selector":".m-loadMoreJobsButton__button",
              "gather_data_selector":'div.m-jobsListItem__container div.m-jobsListItem__dataContainer h2.m-jobsListItem__title a.m-jobsListItem__titleLink',
              "request_wait_time":0.15,
              "title_path":None,
              "company_path":None,
              "salary_path":None,
              }
BASE_KEYWORDS = {
    "locations" : ["vienna"],
    "titlewords": ["machine learning", "machine learning engineer", "machine learning scientist",
                   "ML scientist", "ML engineer", "ML researcher", "ML developer", "ML AI",
                   "AI engineer", "AI scientist", "AI researcher", "AI developer", "AI ML",
                   "data science", "data scientist", "data mining", "web scraping",
                   "data engineer", "data engineering", "data engineering developer", "Python engineer", "DataOps",
                   "data analysis", "data analytics", "data analyst",
                   "graph theory", "network science", "graph database",
                   "business intelligence", "business intelligence analyst", "bi analyst", "business analyst",
                   #"complexity science",
                  ],
    "banned_words": ["manager", "professor", "team leader", "teamleader", "teamleiter", "team leiter", "geschäft",
                    "jurist", "lawyer", "rechsanwalt", "legal", "audit", "advisor", "owner", "officer", "controller",
                    "head of", "director", "leitung", "professor", "professur", "secretary",
                    "ärtzin",
                    "microsoft", "m365", "azure", "cyber security",
                    "praktikum", "praktikant", #"internship", "intern", "trainee",
                    ],
    "banned_capital_words": ["SAP", "HR"],
}
BASE_KEYWORDS["titlewords_dashed"] = [word.replace(" ", "-") for word in BASE_KEYWORDS["titlewords"]]

BASE_RANKINGS ={
    "ranking_pos":{
                #graphs/networks
                "graph":1.5, "network science":2, "graph theory":2, "graph data":1, "graph machine learning": 1,
                "graph database":0.5, "geospatial":0.6, "spatial":0.4, "maps":0.3, "geometry":0.3,
                #general fields
                "machine learning":1, "intelligence":1, "complexity science":2, "math":1, "data":0.35,
                #titles
                "engineer": 0.45, "developer": 0.4, "scientist": 1, "researcher": 0.5, "research": 0.4, "analyst": 0.1,
                #data science
                "data science":1, "data engineering": 0.8, "data management":0.5, "full stack":0.7, "full-stack":0.7,
                "data collection":0.6, "data analysis":0.3, "data mining":0.6, "analytics":0.2, "pipeline":0.1,
                "data modeling": 0.4, "data modelling": 0.4,
                #other fields
                "operations research":1, "optimization":1, "algorithms":1, "numerical":0.1, "modelling":0.5, "modeling":0.5,
                #tech stack
                "python":1, "sql":0.3, "c++":0.1, "algorithm":0.7, "web scraping":0.9, "postgres":0.2, "vector":0.1,
                "knime":0.8, "nlp": 0.5, "neo4j":1, "mysql":0.2, "machine learning engineer":1, "docker":0.2,
                "qlik":0.3,
                #engineering
                "lidar": 0.5, "radar": 0.5, "vision":0.3, "sensor": 0.3, "robot":0.4, "embedded":0.4, "electrical":0.1,
                #details
                "conference":0.7, "home office":0.15, "open source":0.2,
                #languages
                "hungarian":1.3, "hungary":0.5,
                },
    "ranking_pos_capital":{"ETL":1, "ELT":1, "AI":0.5, "ML":0.6, "API":0.3, "REST":0.1, "CI/CD":0.2, "CI CD":0.2, "AWS":0.2,},
    "ranking_neg":{
                    #type of work
                    "consultant":-0.7, "consulting":-0.7, "audit":-1, "risk":-0.5, "control":-1, "holding":-1,
                    "purchasing":-1, "accounting": -1, "accountant": -1, "marketing": -1, "sales": -1, "thesis":-0.5,
                    #high rank
                    "leiter":-1.5, "leader":-0.5, "lead": -1, "manager":-1, "management":-1, "owner":-1, "officer":-1, "head":-0.7,
                    #tech
                    "cyber":-0.5, "security":-0.5, "devops":-0.1, "java":-0.1, "test":-0.3,
                    "web":-0.3, "stack developer":-0.6, "linux":-0.5, "safety":-0.5, "quality":-0.3,
                    #general rank
                    "senior":-0.2, "student":-0.2, "architect":-0.5, "support":-0.5,
                    #work related keywords
                    "product": -0.5, "agile":-0.5, "requirement":-0.5, "scrum":-0.5,
                    "merger": -0.6, "acquisition": -0.6, "real estate": -1, "assurance": -0.5,
                    #other
                    "technik":-1, "dissertation": -1, #"phd": -0.5,
                    },
    "ranking_neg_capital":{"SAP":-1, "HR":-1, "SAS":-0.5,},
    "neutral":[#dataviz
        "visualization", "tableau", "power bi", "dashboard", "d3", "matplotlib", "seaborn", "shiny",
        #data
        "daten", "llm", "quantitative", "quantitative", "big data", "data warehous",#e/ing
        #data software
        "cloudpak", "django", "scala", "spark", "hadoop", "kafka", "airflow", "apache",
        #web
        "html", "javascript", "react", "angular", "node", "flask",
        #IT
        "cloud", "git", "workflow", #"ci/cd", "ci cd",
        #IT software
        "kubernetes", "jenkins", "terraform", "azure", "gcp", "github", "gitlab", "bitbucket",
        "excel", "powerpoint", 
        #other
        "b2c", "b2b", "lean", "kanban", "data-driven", "data driven", "kpi", "customer service", "communication",
        "stakeholder", "marketing", "sales", "banking", "finance", "insurance", "health",
    ]
}

def get_all_keywords(keywords = BASE_KEYWORDS, rankings = BASE_RANKINGS):
    """
    Returns union of keywords (as lists), non capitalized and capitalized.
    """
    
    all_keywords_noncapital = list(set(
        (keywords.get("titlewords", []) +
         keywords.get("banned_words", []) +
         keywords.get("banned_capital_words", []) +
         list(rankings.get("ranking_pos", {}).keys()) +
         list(rankings.get("ranking_neg", {}).keys()) +
         rankings.get("neutral", []))
    ))

    all_keywords_capital = list(set(
        list(rankings.get("ranking_pos_capital", {}).keys()) +
        list(rankings.get("ranking_neg_capital", {}).keys())
    ))

    return all_keywords_noncapital, all_keywords_capital

ALL_KEYWORDS_NONCAPITAL, ALL_KEYWORDS_CAPITAL = get_all_keywords(keywords=BASE_KEYWORDS, rankings=BASE_RANKINGS)

LOCATIONS_DESIRED = ["vienna", "wien", "österreich", "austria"]
LOCATIONS_SECONDARY = ["st. pölten", "sankt pölten", "wiener neudorf", "linz", "krems", "nussdorf", 
                       "klosterneuburg", "schwechat"] #graz, salzburg, innsbruck, #klagenfurt

class BaseScraper:
    def __init__(self, driver=None, rules = BASE_RULES, keywords = BASE_KEYWORDS,
                 rankings = BASE_RANKINGS, salary_bearable = SALARY_BEARABLE, locations = None,
                 locations_desired = LOCATIONS_DESIRED, locations_secondary = LOCATIONS_SECONDARY):
        if driver is None:
            self.driver = webdriver.Firefox()
        else:
            self.driver = driver

        self.time = time.strftime("%Y-%m-%d-%H-%M-%S")
        self.day = self.time[:10]

        self.rules = rules
        self.BASE_RULES = rules

        self.keywords = keywords
        self.BASE_KEYWORDS = keywords

        self.rankings = rankings
        self.BASE_RANKINGS = rankings
        
        self.all_keywords_noncapital, self.all_keywords_capital = get_all_keywords(keywords=keywords, rankings=rankings)

        self.salary_bearable = salary_bearable

        self.locations = locations if locations else keywords.get("locations", LOCATIONS_DESIRED)
        self.LOCATIONS_DESIRED = locations_desired
        self.LOCATIONS_SECONDARY = locations_secondary

    def close_website_popup(self, button_selector, url=None, 
                            click_wait=12.0, pre_click_scroll=False, 
                            post_click_wait = 0.0, post_click_scroll_down=False, 
                            close_driver=True, open_page=True):
        """
        Close cookie popups
        """
        #if driver is None:
        #    driver = webdriver.Firefox()
        driver = self.driver
        if url and open_page:
            driver.get(url)

        try:
            driver.execute_script(SCROLL_1000_SCRIPT)
            WebDriverWait(driver, click_wait).until(
                    expected_conditions.element_to_be_clickable((CSS_SELECTOR, button_selector))
            )
            try:
                if pre_click_scroll:
                    driver.execute_script(SCROLL_DOWN_SCRIPT)
                button = driver.find_element(CSS_SELECTOR, button_selector)
                button.click()
                if post_click_scroll_down:
                    driver.execute_script(SCROLL_DOWN_SCRIPT)

            except (NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException):
                pass

            if post_click_wait:
                time.sleep(post_click_wait)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
        except TimeoutException:
            soup = BeautifulSoup(driver.page_source, 'html.parser')

        finally:
            if close_driver:
                driver.quit()
        return soup
    
    def load_page(self, url, close_popup=True, 
                  load_more_button = True, load_by_scrolling = False,
                  popup_wait=12.0, pre_popup_scroll=True, popup_selector=None,
                  post_popup_close_wait=0.3, post_popup_close_scroll_down=True,
                  action_wait=1.1, first_action_wait = 2.0,
                  post_load_more_wait=0.1,
                  load_more_selector=None,
                  close_driver=False):
        """
        General function for loading all sorts of pages; closing popups, pressing buttons and scrolling if necessary.

        Parameters:
        url: str
            The url of the website to load.
        close_popup: bool
            If True, close the popup window.
        load_more_button: bool
            If True, keep pressing a "Load more" button until it disappears.
        load_by_scrolling: bool
            If True, keep scrolling down until the end of the page.
        popup_wait: float
            Time to wait for the popup to appear.
        pre_popup_scroll: bool
            If True, scroll down before pressing the popup button.
        post_popup_close_wait: float
            Time to wait after closing the popup.
        post_popup_close_scroll_down: bool
            If True, scroll down after closing the popup.
        action_wait: float
            Time to wait after either pressing the "Load more" button, or scrolling down.
        first_action_wait: float
            Time to wait before the first action (pressing the load more button, or scrolling down).
        post_load_more_wait: float
            Time to wait after pressing the "Load more" button.
        close_driver: bool
            If True, close the driver after finishing the process.

        Returns:
        final_page_soup: BeautifulSoup
            The final page soup after all actions have been performed.
        """
        driver = self.driver
        driver.get(url)
        if driver is None:
            driver = webdriver.Firefox()
        if popup_selector is None:
            popup_selector = self.rules["load_page_button_selector"]
        if load_more_selector is None:
            load_more_selector = self.rules["load_page_press_button_until_gone_selector"]
        
        if close_popup:
            self.close_website_popup(popup_selector, url=None, click_wait=popup_wait,
                                     pre_click_scroll=pre_popup_scroll,
                                     post_click_wait=post_popup_close_wait,
                                     post_click_scroll_down=post_popup_close_scroll_down,
                                     close_driver=False, open_page=False)

        if load_more_button:
            final_page_soup = scrape.press_button_until_gone(load_more_selector, url = None,
                                                             first_wait=first_action_wait,
                                                             pre_click_wait=action_wait,
                                                             post_click_wait=post_load_more_wait,
                                                             scroll=True, open_page=False,
                                                             driver=driver, close_driver=False)
        elif load_by_scrolling:
            final_page_soup = scrape.scroll_scrape_website(url=None, driver=driver, close_driver=False,
                                                           wait_time=action_wait, pre_first_scroll_wait=first_action_wait,
                                                           open_page=False)
        else:
            final_page_soup = BeautifulSoup(driver.page_source, 'html.parser')

        if close_driver:
            driver.quit()
        return final_page_soup

    def load_pages(self, urls, close_popup="first", popup_closing_wait=12.0,
                   load_more_button = True, load_by_scrolling = False,
                   post_click_wait = 0.0, close_driver=True, **kwargs):
        driver = self.driver
        if driver is None:
            driver = webdriver.Firefox()
        all_soups = []

        if close_popup in ["none", False]:
            _close_popup_bool = False
        else:
            _close_popup_bool = True

        for i,url in enumerate(urls):
            soup = self.load_page(url, close_popup =_close_popup_bool, popup_wait=popup_closing_wait,
                                  load_more_button = load_more_button, load_by_scrolling=load_by_scrolling,
                                  post_click_wait = post_click_wait, close_driver=False, **kwargs)
            if i==0 and close_popup == "first":
                _close_popup_bool = False
            all_soups.append(soup)

        if close_driver:
            driver.quit()
        return all_soups

    def construct_page_urls(self, base_url = None, locations = None, titlewords = None):
        if base_url is None:
            base_url = self.rules["scraping_base_url"]
        if locations is None:
            locations = self.keywords["locations"]
        if titlewords is None:
            titlewords = self.keywords["titlewords"]
        links = urls.urls_builder(base_url = base_url, slash_elements_list = [titlewords, locations],
                                  zipped = True, all_combinations = True)
        links = list(set(links)) #Don't include duplicates
        return links

    def next_page_logic(self, input, **kwargs):
        """input: typically a soup or HTML element, possibly dict or string"""
        pass

    def salary_number_from_str(self, text, keywords=[],
                               remove_chars = ['.'], lengths=[6,5]):
        if type(text) != str:
            return None
        for char in remove_chars:
            text_cleaned = text.replace(char, "")
        if not keywords:
            for length in lengths:
                #Search for length-digit numbers
                value = re.search(rf'\d{{{length}}}', text_cleaned)
                if value:
                    return int(value.group())
        else:
            if any([keyword in text for keyword in keywords]):
                for length in lengths:
                    value = re.search(rf'\d{{{length}}}', text_cleaned)
                    if value:
                        return int(value.group())
        return None
    
    def salary_regex(self, text, regexes=[r'\d{6},\d{2}', r'\d{5},\d{2}',  r'\d{6}', r'\d{5}'],
                     decimal_separator=","):
        for regex in regexes:
            value = re.search(regex, text)
            if value:
                try:
                    return int(value.group())
                except ValueError:
                    return int(float(value.group().replace(decimal_separator,".")))
        return None

    def salary_from_text(self, text, keywords={"annual":["jährlich", "yearly", "per year", "annual", "jährige", "pro jahr", "p.a."],
                                               "monthly":["monatlich", "monthly", "per month", "pro monat"]},
                                               clarity_comma_char=".", decimal_separator=",", conversion_rate=14):
        if type(text) != str:
            return None
        text = text.lower()
        salary = {}
        if "annual" in keywords.keys():
            value = self.salary_number_from_str(text, keywords["annual"], remove_chars=[clarity_comma_char], lengths=[6,5])
            if value:
                salary["annual"] = value
        if (not salary) and ("monthly" in keywords.keys()):
            value = self.salary_regex(text.replace(clarity_comma_char, ""), decimal_separator=decimal_separator,
                                      regexes=[r'\d{{4}}{0}\d{{2}}'.format(decimal_separator)])
            if not value:
                value = self.salary_number_from_str(text, keywords["monthly"], remove_chars=[clarity_comma_char], lengths=[4])
            if value:
                salary["monthly"] = value
        if not salary:
            value = self.salary_regex(text.replace(clarity_comma_char, ""), decimal_separator=decimal_separator,
                                      regexes=[r'\d{{6}}{0}\d{{2}}'.format(decimal_separator), r'\d{{5}}{0}\d{{2}}'.format(decimal_separator), r'\d{6}', r'\d{5}'])
            if value:
                salary["annual"] = value
            else:
                value = self.salary_regex(text.replace(clarity_comma_char, ""), decimal_separator=decimal_separator,
                                          regexes=[r'\d{{4}}{0}\d{{2}}'.format(decimal_separator), r'\d{4}'])
                if value:
                    salary["monthly"] = value
            
        #Conversion
        if list(salary.keys()) == ["annual"]:
            salary["monthly"] = int(salary["annual"]/conversion_rate)
        elif list(salary.keys()) == ["monthly"]:
            salary["annual"] = int(salary["monthly"]*conversion_rate)

        if salary.keys() == []:
            return None
        return salary

    def salary_from_description(self, text,
                                regexes = [r'(Salary|Gehalt|Compensation|Vergütung):.*',
                                           r'\b(Gross|Brutto|Net|Netto)\b:.*',
                                           r'(\d{5}[.,]\d+)(?:(?!\d{5}[.,]?\d*).)*?\b(netto|brutto|gross)\b',#select last such number
                                           r'(\d{2}[.,]\d{3}[.,]\d+)(?:(?!\d{2}[.,]\d{3}[.,]\d*).)*?\b(netto|brutto|gross)\b',
                                           r'(\d{4}[.,]\d+)(?:(?!\d{4}[.,]?\d*).)*?\b(netto|brutto|gross)\b',
                                           r'(\d{1}[.,]\d{3}[.,]\d+)(?:(?!\d{1}[.,]\d{3}[.,]\d*).)*?\b(netto|brutto|gross)\b',
                                           r'(\d{5})(?:(?!\d{5}).)*?\b(netto|brutto|gross)\b',
                                           r'(\d{2}[.,]\d{3})(?:(?!\d{2}[.,]\d{3}).)*?\b(netto|brutto|gross)\b',
                                           r'(\d{5}[.,]\d+)(?:(?!\d{5}[.,]?\d*).)*?\b(net|taxes|tax)\b',
                                           r'(\d{4}[.,]\d+)(?:(?!\d{4}[.,]?\d*).)*?\b(net|taxes|tax)\b',
                                           r'(\d{1}[.,]\d{3})(?:(?!\d{1}[.,]\d{3}).)*?\b(netto|brutto|gross)\b',
                                           r'\d{4,5}[.,]\d{2}',
                                           r'(\d{5})(?:(?!\d{5}).)*?\b(net|taxes|tax)\b',
                                           ],
                                **kwargs):
        if type(text) != str:
            return None
        for regex in regexes:
            salary_section = re.search(regex, text, flags=re.IGNORECASE)
            if salary_section:
                salary = self.salary_from_text(salary_section.group(), **kwargs)
                return salary
        return None

    def salary_points(self, salary, salary_bearable = SALARY_BEARABLE, salary_ratio = 0.15/100,
                      high_dropoff = True, dropoff_bearable_ratio = 1.6):
        points = (salary-salary_bearable)*salary_ratio
        if high_dropoff & (salary > salary_bearable*dropoff_bearable_ratio):
            max_points = (salary_bearable*dropoff_bearable_ratio-salary_bearable)*salary_ratio
            points = 2 * max_points - points
        return points

    def process_posting_soups(self, soups, pattern, website = "",
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
                    salary_versions = self.salary_from_text(salary)

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

    def save_data(self, data, path = "source/save/postings/", name="", with_date = True, verbose = False):
        #check if path exists
        if not os.path.exists(path):
            os.makedirs(path)
        if not name:
            name = self.rules["website"]
        if with_date:
            date = time.strftime("%Y-%m-%d-%H-%M-%S")
            name = f"{name}_{date}"
        with open(f"{path}{name}.json", "w", encoding="utf-8") as file:
            if type(data) in [dict, list, str]:
                json.dump(data, file, indent=4, ensure_ascii=False)
            else:
                if verbose:
                    print(f"Could not save data of type {type(data)}")
    
    def filter_postings(self, postings:dict, banned_words=None, banned_capital_words=None):
        if not banned_words:
            banned_words = self.keywords.get("banned_words", [])
        if not banned_capital_words:
            banned_capital_words = self.keywords.get("banned_capital_words", [])
        filtered_postings = {}
        for id, posting in postings.items():
            title = posting["title"]
            if any([word in title.lower() for word in banned_words]):
                continue
            if any([word in title for word in banned_capital_words]):
                continue
            filtered_postings[id] = posting
        return filtered_postings
    
    def check_locations(self, locations_list, locations_desired=["vienna", "wien", "österreich"]):
        if not locations_desired:
            locations_desired = self.__dict__.get("LOCATIONS_DESIRED", LOCATIONS_DESIRED)
        for location in locations_list:
            for desired in locations_desired:
                if desired.lower() in location.lower(): #in the string, e.g. "wien" in "wien 04"
                    return True
        return False

    def rank_postings(self, postings:dict, keyword_points=None, desc_ratio = 0.3,
                      salary_bearable = None, salary_ratio = 0.15/100, 
                      locations_desired=None, locations_secodary=None):
        if not salary_bearable:
            salary_bearable = getattr(self, "salary_bearable", SALARY_BEARABLE)
        if not keyword_points:
            keyword_points = getattr(self, "rankings", BASE_RANKINGS)
        if not locations_desired:
            locations_desired = getattr(self, "LOCATIONS_DESIRED", LOCATIONS_DESIRED)
        if not locations_secodary:
            locations_secodary = getattr(self, "LOCATIONS_SECONDARY", LOCATIONS_SECONDARY)

        for id, posting in postings.items():
            title = posting["title"] if "title" in posting.keys() else ""
            description = posting["description"] if "description" in posting.keys() else ""
            salary = posting["salary_monthly_guessed"]
            points = 0
            for keyword, value in keyword_points["ranking_pos"].items():
                if keyword in title.lower():
                    points += value
                if keyword in description.lower():
                    points += value*desc_ratio
            for keyword, value in keyword_points["ranking_pos_capital"].items():
                if keyword in title:
                    points += value
                if keyword in description:
                    points += value*desc_ratio
            for keyword, value in keyword_points["ranking_neg"].items():
                if keyword in title.lower():
                    points += value
                if keyword in description.lower():
                    points += value*desc_ratio
            for keyword, value in keyword_points["ranking_neg_capital"].items():
                if keyword in title:
                    points += value
                if keyword in description:
                    points += value*desc_ratio
            
            if salary:
                points += self.salary_points(salary, salary_bearable=salary_bearable, salary_ratio=salary_ratio,
                                             high_dropoff=True, dropoff_bearable_ratio=2.0)
            
            if posting.get("locations"):
                if not self.check_locations(posting["locations"], locations_desired=locations_desired):
                    points -= 1
                    if not self.check_locations(posting["locations"], locations_desired=locations_secodary):
                        points -= 1

            postings[id]["points"] = round(points, 3)
        return postings

    def find_keywords(self, text, non_capital = None, capital = None, sort=True, rankings = None):
        if not non_capital:
            non_capital = getattr(self, "all_keywords_noncapital", ALL_KEYWORDS_NONCAPITAL)
        if not capital:
            capital = getattr(self, "all_keywords_capital", ALL_KEYWORDS_CAPITAL)
        if sort and (not rankings):
            rankings = getattr(self, "rankings", BASE_RANKINGS)

        found = []
        for keyword in non_capital:
            if keyword in text.lower():
                found.append(keyword)
        for keyword in capital:
            if keyword in text:
                found.append(keyword)

        if sort:
            found = sorted(found,
                key=lambda k: -abs(rankings.get("ranking_pos", {}).get(k, 0) or rankings.get("ranking_neg", {}).get(k, 0))
            )
        return found
    
    def find_keywords_in_postings(self, postings:dict, description_key = "description",
                                  non_capital = None, capital=None, sort=True, rankings = None):
        if not non_capital:
            non_capital = getattr(self, "all_keywords_noncapital", ALL_KEYWORDS_NONCAPITAL)
        if not capital:
            capital = getattr(self, "all_keywords_capital", ALL_KEYWORDS_CAPITAL)

        for id, posting in postings.items():
            postings[id]["keywords"] = []
            if description_key in posting.keys():
                text = posting[description_key]
                keywords = self.find_keywords(text, non_capital=non_capital, capital=capital,
                                              sort=sort, rankings=rankings)
                postings[id]["keywords"] = keywords
        return postings

    def gather_data(self, close_driver=True,
                    url_links = [],
                    posting_id = False,
                    posting_id_path = "href", #can be None
                    posting_id_regex = r'\d+',
                    titles = False,
                    companies = False,
                    salary = False):
        """
        url_links: list | function
        """
        pattern = self.rules["gather_data_selector"]
        website = self.rules["website"]
        usecase = self.rules["usecase"]
        title_path = None
        company_path = None
        salary_path = None
        if titles:
            title_path = self.rules["title_path"]
        if companies:
            company_path = self.rules["company_path"]
        if salary:
            salary_path = self.rules["salary_path"]

        if type(url_links) == function:
            url_links = url_links()
        if url_links == []:
            url_links = self.construct_page_urls(self.rules["scraping_base_url"])

        if usecase in ["http", "https"]:
            request_wait_time = self.rules["request_wait_time"] if "request_wait_time" in self.rules.keys() else 0.3
            soups = scrape.requests_responses(url_links, https=True if usecase=="https" else False,
                                              return_kind="soups", wait_time=request_wait_time)
        elif usecase in ["selenium", "http_selenium"]:
            driver = self.driver
            if driver is None:
                driver = webdriver.Firefox()
            soups = self.load_pages(url_links, close_popup="first", close_driver=False)
        else:
            raise ValueError("Usecase not implemented")

        postings = self.process_posting_soups(soups, pattern, posting_id=posting_id, website=website,
                                      posting_id_path=posting_id_path, posting_id_regex=posting_id_regex,
                                      title_path=title_path, company_path=company_path, salary_path=salary_path)
        
        postings = self.filter_postings(postings)
        postings = self.rank_postings(postings)
        postings = self.find_keywords_in_postings(postings)
        if titles:
            title_list = [posting["text"] for posting in postings.values()]
        if companies:
            company_list = list(set([posting["company"] for posting in postings.values()]))

        if close_driver:
            driver.quit()

        if titles:
            if companies:
                return postings, title_list, company_list
            return postings, title_list
        elif companies:
            return postings, company_list
        return postings


class KarriereATScraper(BaseScraper):
    def __init__(self, driver="", rules = BASE_RULES, keywords = BASE_KEYWORDS,
                 rankings = BASE_RANKINGS, salary_bearable = SALARY_BEARABLE, locations = None,
                 locations_desired = LOCATIONS_DESIRED, locations_secondary = LOCATIONS_SECONDARY):
        """
        If Selenium is used, the driver argument should be None or a previously opened driver
        If it is not used, the driver argument should be something other than None
        """
        rules["website"] = "karriere.at"
        rules["usecase"] = "https"
        rules["scraping_base_url"] = "https://www.karriere.at/jobs"
        rules["request_wait_time"] = 0.16
        if driver or type(driver) == type(None):
            keywords["locations"] = ["wien-und-umgebung"]
            locations = ["wien-und-umgebung"]
            #keywords["titlewords"] = keywords["titlewords_dashed"]
        else:
            keywords["locations"] = ["wien und umgebung"]
            locations = ["wien und umgebung"]

        self.X_CSRF_TOKEN = "GVJiHEzc3AZ3syhOq8TV1DpRECCEvAnDIzJ3hGSW"
        super().__init__(driver=driver, rules=rules, keywords=keywords, rankings=rankings,
                         salary_bearable=salary_bearable, locations=locations,
                         locations_desired=locations_desired, locations_secondary=locations_secondary
                         )
        
    def load_job(self, url, close_popup=False,
                 popup_wait=5.0, post_click_wait=1.0,
                 close_driver=True, return_url=False):
        """ Warning: outdated method """
        popup_selector = self.rules["load_page_button_selector"]
        driver = self.driver
        if driver is None:
            driver = webdriver.Firefox()
        driver.get(url)
        
        if close_popup:
            soup = self.close_website_popup(popup_selector, url = url, click_wait=popup_wait,
                                            post_click_wait=post_click_wait, post_click_scroll_down=True,
                                            close_driver=False, open_page=False)
        if close_driver:
            driver.quit()

        if return_url:
            return soup, url
        return soup

    def load_jobs(self, urls, close_popup=False,
                  popup_wait=5.0, post_click_wait=1.0,
                  close_driver=True, return_urls=False):
        """ Warning: outdated method """
        driver = self.driver
        if driver is None:
            driver = webdriver.Firefox()
        soups = []
        links = []

        for url in urls:
            if return_urls:
                soup, url = self.load_job(url, close_popup=close_popup, 
                                          popup_wait=popup_wait, post_click_wait=post_click_wait, 
                                          close_driver=False, return_url=True)
                links.append(url)
            else:
                soup = self.load_job(url, driver=driver, close_popup=close_popup, 
                                     popup_wait=popup_wait, post_click_wait=post_click_wait, 
                                     close_driver=False, return_url=False)
            soups.append(soup)

        if close_driver:
            driver.quit()

        if return_urls:
            return soups, links
        return soups

    def load_page(self, url, close_popup=True,
                  popup_wait=12.0, pre_click_scroll=True,
                  post_popup_close_wait=0.3,
                  first_load_more_wait = 0.1, post_load_more_wait=0.1,
                  close_driver=True, **kwargs):
        """ Warning: outdated method """

        popup_selector = self.rules["load_page_button_selector"]
        load_more_selector = self.rules["load_page_press_button_until_gone_selector"]
        final_page_soup = super().load_page(url, close_popup=close_popup,
                                            load_more_button=True, load_by_scrolling=False,
                                            popup_wait=popup_wait, pre_popup_scroll=pre_click_scroll,
                                            popup_selector=popup_selector,
                                            post_popup_close_wait=post_popup_close_wait,
                                            post_popup_close_scroll_down=True,
                                            action_wait=first_load_more_wait, first_action_wait=first_load_more_wait,
                                            post_load_more_wait=post_load_more_wait,
                                            load_more_selector=load_more_selector,
                                            close_driver=close_driver,
                                            **kwargs)

        return final_page_soup

    def data_gather_outdated_selenium(self, close_driver=True,
                    descriptions = False):
        """ Warning: outdated method """

        pattern = self.rules["gather_data_selector"]
        website = self.rules["website"]
        #usecase = self.rules["usecase"]
        #title_path = self.rules["title_path"]
        #company_path = self.rules["company_path"]
        if driver is None:
            driver = webdriver.Firefox()
        links = self.construct_page_urls()
        soups = self.load_pages(links, close_popup="first", close_driver=False)

        postings = {}
        for soup in soups:
            selects = soup.select(pattern)
            for select in selects:
                id = re.search(r'\d+', select["href"]).group()
                if id not in postings.keys():
                    title = select.text
                    if title:
                        title = title.strip()
                    postings[id] = {"title": title, "url": select["href"],
                                    "source": website, "id": id}

        if descriptions:
            jobs_url = [posting["url"] for posting in postings.values()]
            soups,returned_urls = self.load_jobs(jobs_url, popup_wait=2.2, close_driver=False, return_urls=True)
            ids = [re.search(r'\d+', url).group() for url in returned_urls]

            for i,soup in enumerate(soups):
                description = soup.find("div", class_="m-jobContent__jobText m-jobContent__jobText--standalone")
                if description:
                    description = description.text.strip()
                postings[ids[i]]["description"] = description

        if close_driver:
            driver.quit()
        return postings
    
    def gather_data(self, descriptions=False, save_data=False, verbose=False):
        website = self.rules["website"]
        locations = self.keywords["locations"]
        titlewords = self.keywords["titlewords"] #expected not to have dashes, but spaces
        wait_time = self.rules["request_wait_time"]
        pairs = [(title, location) for title in titlewords for location in locations]
        postings = {}
        for pair in pairs:
            base_url = 'https://www.karriere.at/jobs?keywords='+pair[0]+'&location='+pair[1]
            path = '/jobs?keywords='+pair[0]+'&location='+pair[1]
            referer = 'https://www.karriere.at/jobs/'+pair[0].replace(' ','-')+'/'+pair[1].replace(' ','-')
            responses = scrape.requests_responses_with_cookies(base_url= base_url,
                                       pages=["&page=" + str(i) for i in range(1,40)],
                                       base_path = path,
                                       referer = referer,
                                       wait_time=wait_time,
                                       headers_more = {
                                           "Priority": "u=1, i",
                                           "X-CSRF-Token": self.X_CSRF_TOKEN,
                                           "X-Requested-With": "XMLHttpRequest",
                                       },
                                       return_kind='responses',
                                       verbose=verbose)
            if responses:
                for response in responses:
                    content = json.loads(response.text)
                    items = content['data']['jobsSearchList']['activeItems']['items']
                    for i in range(len(items)):
                        if 'jobsItem' in items[i]:
                            posting = items[i]['jobsItem']
                            locs = posting['locations']
                            salary_read = self.salary_from_text(posting['salary'])
                            postings.update({(website+str(posting['id'])):{
                                            "title": posting['title'],
                                            "company": posting['company']['name'],
                                            "locations": [loc['name'] for loc in locs],
                                            "salary": posting['salary'],
                                            "salary_monthly_guessed": salary_read["monthly"] if salary_read else None,
                                            "salary_guessed": salary_read,
                                            "source": website,
                                            "isActive": posting['isActive'],
                                            "isHomeOffice": posting['isHomeOffice'],
                                            "employmentTypes": posting['employmentTypes'],
                                            "url": posting['link'],
                                            "snippet": posting['snippet'],
                                            "collected_on": self.day,
                                            "date": posting['date'],
                                            "id": posting['id']}
                                            })
                        else:
                            if ('alarmDisruptor' not in items[i]) and ('contentAd' not in items[i]) and ('bsAd' not in items[i]):
                                if verbose:
                                    print(items[i])
                            continue

        postings = self.filter_postings(postings)

        if descriptions:
            jobs_url = [posting["url"] for posting in postings.values()]
            ids = [re.search(r'\d+', url) for url in jobs_url if re.search(r'\d+', url)]
            ids = ["/"+ str(id.group()) for id in ids]
            responses = scrape.requests_responses_with_cookies(base_url='https://www.karriere.at/jobs',
                                       base_path = '/jobs',
                                       referer = 'https://www.karriere.at/jobs/machine-learning/wien-und-umgebung',
                                       pages=ids,
                                       headers_more = {
                                           "Priority": "u=1, i",
                                           "X-CSRF-Token": self.X_CSRF_TOKEN,
                                           "X-Requested-With": "XMLHttpRequest",
                                       },
                                       return_kind='responses')
            if responses:
                for response in responses:
                    content = (json.loads(response.text))
                    posting = content['data']['jobDetailContent']['jobContent']['text']
                    id = content['data']['jobDetailContent']['jobHeader']['job']['id']
                    id = website+str(id)
                    if id in postings.keys():
                        if posting:
                            posting = BeautifulSoup(posting, 'html.parser').get_text()
                            postings[id]["description"] = posting
                    else:
                        if verbose:
                            print(f"Could not find id {id} in saved postings - likely programming error")
                postings = self.find_keywords_in_postings(postings)

        postings = self.rank_postings(postings)
        postings = {k: v for k, v in sorted(postings.items(), key=lambda item: item[1]["points"], reverse=True)}
        if save_data:
            self.save_data(postings, name=f"karriere_at", with_date=True)
        return postings

    
class RaiffeisenScraper(BaseScraper):
    def __init__(self, driver="", rules = BASE_RULES, keywords = BASE_KEYWORDS,
                  rankings = BASE_RANKINGS, salary_bearable = SALARY_BEARABLE, locations = None,
                 locations_desired=LOCATIONS_DESIRED, locations_secondary=LOCATIONS_SECONDARY):
        rules["website"] = "raiffeisen_international"
        rules["usecase"] = "http"
        rules["scraping_base_url"] = "https://jobs.rbinternational.com/search/?q="
        rules["jobs_base_url"] = "https://jobs.rbinternational.com"
        rules['gather_data_selector'] = 'a.jobTitle-link'
        rules['more_pages_url_extension'] = "&sortColumn=referencedate&sortDirection=desc&startrow="
        rules['description_selector'] = 'ul'
        rules["request_wait_time"] = 0.16 if "request_wait_time" not in rules.keys() else rules["request_wait_time"]
        
        for key, value in BASE_RULES.items():
            if key not in rules.keys():
                rules[key] = value

        if not keywords:
            keywords = BASE_KEYWORDS
        keywords["titlewords"] += ["machine", "engineer", "scientist"]
        
        super().__init__(driver=driver, rules=rules, keywords=keywords, rankings=rankings,
                         salary_bearable=salary_bearable, locations=locations,
                         locations_desired=locations_desired, locations_secondary=locations_secondary, 
                         )

    def construct_page_urls(self, base_url = None, titlewords = None):
        if base_url is None:
            base_url = self.rules["scraping_base_url"]
        if titlewords is None:
            titlewords = self.keywords["titlewords"]
        links = []
        for titleword in titlewords:
            links.append(base_url + titleword)
        links = list(set(links)) #Don't include duplicates
        return links
    
    def next_page_logic(self, input:BeautifulSoup, pattern):
        """input: typically a soup or HTML element, possibly dict or string"""
        if not isinstance(input, BeautifulSoup):
            input = BeautifulSoup(input, 'html.parser')
        selects = input.select(pattern)
        if len(selects) == 50 or len(selects) == 25:
            return True
        return False

    def process_posting_soups(self, soups, pattern, website="", jobs_base_url=None):
        #could also use .select('.pagination') or .select('ul.pagination') counting
        if not website:
            website = self.rules["website"]
        if jobs_base_url is None:
            jobs_base_url = self.rules["jobs_base_url"]
        postings = {}
        for soup in soups:
            selects = soup.select(pattern)
            for select in selects:
                title = select.text
                url = jobs_base_url + select["href"]
                id = re.search(r'/\d+/$', url).group().replace("/", "")
                id = website + id
                if id not in postings.keys():
                    title = select.text
                    if title:
                        title = title.strip()
                    postings[id] = {"title": title, "url": url,
                                    "company": "Raiffeisen International",
                                    "source": website, "id": id}
        return postings
        
    def clean_variables(self, variables):
        if type(variables) == str:
            variables = variables.strip().replace("\n", " ").replace("\t", " ").replace("\r", " ").replace("\xa0", " ")
        elif type(variables) == list:
            for (i, variable) in enumerate(variables):
                variables[i] = variable.strip().replace("\n", " ").replace("\t", " ").replace("\r", " ").replace("\xa0", " ") if variable else None
        return variables
    
    def soup_descriptions(self, id_soup_dicts, verbose=False):
        descriptions = {}
        for id, soup in id_soup_dicts.items():
            posting = soup.select("div.joblayouttoken.rtltextaligneligible.displayDTM") #TODO
            for i in posting:
                if i.select("ul"):
                    break
            posting = i
            contexts = posting.select("ul")
            contexts = [context for context in contexts if context.attrs=={}]
            if len(contexts) not in [3,4]:
                if verbose:
                    #print(f"Contexts length not 4, but {len(contexts)}; something incorrect. Contexts: {contexts}")
                    pass

            role = contexts[0].text if contexts else None
            requirements = contexts[1].text if len(contexts)>1 else None
            benefits = contexts[2].text if len(contexts)>2 else None
            nice_to_have = None

            if len(contexts)==3:
                benefits = contexts[2].text
            elif len(contexts)==4:
                nice_to_have = contexts[2].text
                benefits = contexts[3].text
            elif len(contexts)>4:
                #join all contexts
                benefits = "\n ".join([context.text for context in contexts[2:]])

            description = posting.text
            salary = None
            if benefits:
                salary = self.salary_from_description(benefits, decimal_separator=".", clarity_comma_char=",")
                if not salary:
                    salary = self.salary_from_description(benefits, decimal_separator=",", clarity_comma_char=".")
                salary_monthly = salary["monthly"] if salary else None

            role, requirements, nice_to_have, benefits, description = self.clean_variables([role, requirements, nice_to_have, benefits, description])
            descriptions[id] = {"role": role, "requirements": requirements,
                                "salary_guessed": salary, "salary_monthly_guessed": salary_monthly,
                                "nice_to_have": nice_to_have, "benefits": benefits,
                                "description": description}
        return descriptions
                

    def gather_data(self, url_links=[], descriptions=False, verbose=False):
        titles_pattern = self.rules["gather_data_selector"]
        website = self.rules["website"]
        usecase = self.rules["usecase"]
        request_wait_time = self.rules["request_wait_time"] if "request_wait_time" in self.rules.keys() else 0.16
        more_pages_url_extension = self.rules["more_pages_url_extension"]
        jobs_base_url = self.rules["jobs_base_url"]


        if url_links == []:
            url_links = self.construct_page_urls(self.rules["scraping_base_url"])

        soups = []
        for url in url_links:
            soup = scrape.requests_responses([url], https=True if usecase=="https" else False,
                                              return_kind="soups", wait_time=request_wait_time)[0]
            soups.append(soup)
            row = 25
            get_next_page = self.next_page_logic(soup, titles_pattern)
            while get_next_page:
                if verbose:
                    print(f"Getting next page for {url}")
                next_page = url + more_pages_url_extension + str(row)
                soup = scrape.requests_responses([next_page], https=True if usecase=="https" else False,
                                                  return_kind="soups", wait_time=request_wait_time)[0]
                soups.append(soup)
                get_next_page = self.next_page_logic(soup, titles_pattern)
                row += 25
                
        postings = self.process_posting_soups(soups, titles_pattern, website=website,
                                      jobs_base_url=jobs_base_url)
        postings = self.filter_postings(postings)

        if descriptions:
            urls = [posting["url"] for posting in postings.values()]
            ids = [website+re.search(r'/\d+/$', url).group().replace("/", "") for url in urls]
            soups = scrape.requests_responses(urls, https=True if usecase=="https" else False,
                                              return_kind="soups", wait_time=request_wait_time)
            ids_soups = {id:soup for id,soup in zip(ids, soups)}
            descriptions = self.soup_descriptions(ids_soups, verbose=verbose)
            for id, posting in descriptions.items():
                postings[id] = {'id':id, 'title':postings[id]["title"],
                                'company':postings[id]["company"],
                                **posting, 'url':postings[id]["url"],
                                'source':postings[id]["source"],
                                "collected_on": self.day,
                                }
        
        postings = self.rank_postings(postings)
        postings = self.find_keywords_in_postings(postings)
        return postings