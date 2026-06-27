"""Scrapers for job posting sites."""

import time
from copy import deepcopy
from typing import Callable, List, Tuple

try:
    from selenium import webdriver
except ModuleNotFoundError:
    webdriver = None
from jobscraping.config.configs import (
    BASE_KEYWORD_SCORING,
    BASE_PHRASES,
    LOCATIONS_DESIRED,
    LOCATIONS_SECONDARY,
    RELATIVE_POSTINGS_PATH,
    SALARY_BEARABLE,
)
from jobscraping.config.constants import BASE_RULES
from jobscraping.io.files_io import save_data
from jobscraping.processing.attributes import (
    analyze_postings_language,
    check_locations,
    find_keywords,
    find_keywords_in_postings,
    rank_postings,
    salary_from_description,
    salary_from_text,
    salary_points,
)
from jobscraping.processing.postings_utils import (
    filter_postings,
    process_data,
    process_posting_soups,
)
from jobscraping.processing.transformations import apply_filters_transformations
from jobscraping.scrapers import scrape
from jobscraping.utils import urls

GET_HEIGHT_SCRIPT = "return document.body.scrollHeight"
SCROLL_DOWN_SCRIPT = "window.scrollTo(0, document.body.scrollHeight);" #scroll to height value of the bottom of the page
SCROLL_1000_SCRIPT = "window.scrollTo(0, 1000);"
CSS_SELECTOR = "css selector" #can use instead: from selenium.webdriver.common.by import By, then By.CSS_SELECTOR

def get_all_keywords(keywords=None):  # rankings = BASE_KEYWORD_SCORING
    """
    Returns union of keywords (as lists), non capitalized and capitalized.
    """
    if keywords is None:
        keywords = BASE_PHRASES
    all_keywords_noncapital = list(set(
        (keywords.get("titlewords", []) +
         keywords.get("banned_words", []) +
         keywords.get("banned_capital_words", []) +
         keywords.get("description_keywords_order", []))
         #TODO add from rankings the ones with ignore flag
    ))

    all_keywords_capital = list(set(
        keywords.get("banned_capital_words", [])
        #TODO fix
    ))

    return all_keywords_noncapital, all_keywords_capital
#ALL_KEYWORDS_NONCAPITAL, ALL_KEYWORDS_CAPITAL = get_all_keywords(keywords=BASE_PHRASES)


class BaseScraper: #Make abstract?
    """Base scraper with shared helpers for loading and processing postings."""
    def __init__(
        self,
        driver=None,
        rules=None,
        keywords=None,
        extra_keywords=None,
        extra_titlewords=None,
        extra_locations=None,
        rankings=None,
        salary_bearable=SALARY_BEARABLE,
        locations=None,
        locations_desired=None,
        locations_secondary=None,
        transformations=None,
    ):
        if driver is None:
            if webdriver is None:
                raise ModuleNotFoundError("selenium is required to create a webdriver")
            self.driver = webdriver.Firefox()
        else:
            self.driver = driver

        _time = time.time()
        self.time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(_time))
        self.day = self.time[:10]
        self.business_day = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(_time - 8*(60*60)))[:10] #8hrs shift

        if rules is None:
            rules = deepcopy(BASE_RULES)
        else:
            rules = deepcopy(rules)
        self.rules = rules
        self.BASE_RULES = rules

        if keywords is None:
            keywords = deepcopy(BASE_PHRASES)
        else:
            keywords = deepcopy(keywords)
        self.keywords = keywords

        if extra_keywords is None:
            extra_keywords = {}
        if extra_keywords:
            for key_type, key_values in extra_keywords.items():
                self.keywords[key_type] = list(set(self.keywords.get(key_type, []) + key_values))

        if extra_titlewords is None:
            extra_titlewords = []
        if extra_titlewords:
            self.keywords["titlewords"] = list(set(self.keywords.get("titlewords", []) + extra_titlewords))
        locations = locations if locations else keywords.get("locations", LOCATIONS_DESIRED)

        if extra_locations is None:
            extra_locations = []
        if extra_locations:
            locations = list(set(locations + extra_locations))
        self.keywords["locations"] = locations
        self.BASE_PHRASES = deepcopy(self.keywords)

        #TODO same with rankings
        if rankings is None:
            rankings = deepcopy(BASE_KEYWORD_SCORING)
        else:
            rankings = deepcopy(rankings)
        self.rankings = rankings
        self.BASE_RANKINGS = rankings
        #self.signed_rankings = rankings.get("ranking_case_sensitive", {}).copy().update(rankings.get("ranking_lowercase", {}))
        
        self.all_keywords = self.keywords.get("description_keywords_order", [])
        self.description_keywords_order = self.keywords.get("description_keywords_order", [])

        self.salary_bearable = salary_bearable

        self.locations = locations
        if locations_desired is None:
            locations_desired = list(LOCATIONS_DESIRED)
        if locations_secondary is None:
            locations_secondary = list(LOCATIONS_SECONDARY)
        self.locations_desired = locations_desired
        self.locations_secondary = locations_secondary

        if transformations is None:
            transformations = []
        self.transformations = transformations

    def _construct_page_urls(self, base_url = None, locations = None, titlewords = None):
        if base_url is None:
            base_url = self.rules["scraping_base_url"]
        if locations is None:
            locations = self.keywords["locations"]
        if titlewords is None:
            titlewords = self.keywords["titlewords"]
        return urls.urls_builder(base_url = base_url, slash_elements_list = [titlewords, locations],
                                  zipped = True, all_combinations = True, no_duplicates = True)

    def _close_website_popup(self, button_selector, url=None, 
                            click_wait=12.0, pre_click_scroll=False, 
                            post_click_wait = 0.0, post_click_scroll_down=False, 
                            close_driver=True, open_page=True):
        """
        Close cookie popups
        """
        #if driver is None:
        #    driver = webdriver.Firefox()
        driver = self.driver
        return scrape.close_website_popup(driver, button_selector, url=url, click_wait=click_wait,
                                          pre_click_scroll=pre_click_scroll, post_click_wait=post_click_wait,
                                          post_click_scroll_down=post_click_scroll_down,
                                          close_driver=close_driver, open_page=open_page)
    
    def _load_page(self, url, close_popup=True, close_popup_method: Callable = None,
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
        close_popup_method: Callable
            The method to use for closing the popup. By default, uses close_website_popup,
                but can be replaced e.g. in site scraper classes.
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
        if not close_popup_method:
            close_popup_method = getattr(self, "close_popup_method", None) or self._close_website_popup
        return scrape.load_page(driver, url, close_popup=close_popup, load_more_button = load_more_button,
                                close_popup_method = close_popup_method,
                                load_by_scrolling = load_by_scrolling, popup_wait=popup_wait,
                                pre_popup_scroll=pre_popup_scroll, popup_selector=popup_selector,
                                post_popup_close_wait=post_popup_close_wait,
                                post_popup_close_scroll_down=post_popup_close_scroll_down,
                                action_wait=action_wait, first_action_wait = first_action_wait,
                                post_load_more_wait=post_load_more_wait,
                                load_more_selector=load_more_selector,
                                close_driver=close_driver)

    def _load_pages(self, page_urls, close_popup="first", popup_closing_wait=12.0,
                   page_load_method: Callable = None,
                   load_more_button = True, load_by_scrolling = False,
                   post_click_wait = 0.0, close_driver=True, **kwargs):
        driver = self.driver
        if not page_load_method:
            page_load_method = getattr(self, "page_load_method", None) or self._load_page
        return scrape.load_pages(driver, page_urls, close_popup=close_popup, popup_closing_wait=popup_closing_wait,
                                page_load_method=page_load_method,
                                load_more_button = load_more_button, load_by_scrolling = load_by_scrolling,
                                post_click_wait = post_click_wait, close_driver=close_driver, **kwargs)

    def next_page_logic(self, data, **kwargs):
        """data: typically a soup or HTML element, possibly dict or string"""
        # TODO
        return None

    def _salary_from_text(
        self,
        text,
        keywords=None,
        clarity_comma_char=".",
        decimal_separator=",",
        conversion_rate=12,
    ):
        if keywords is None:
            keywords = {
                "annual": [
                    "jährlich",
                    "yearly",
                    "per year",
                    "annual",
                    "jährige",
                    "pro jahr",
                    "p.a.",
                ],
                "monthly": ["monatlich", "monthly", "per month", "pro monat"],
            }
        return salary_from_text(text, keywords=keywords, clarity_comma_char=clarity_comma_char,
                                decimal_separator=decimal_separator, conversion_rate=conversion_rate)

    def _salary_from_description(self, text, regexes=None, method: Callable = None, **kwargs):
        if not isinstance(text, str):
            return None
        if regexes is None:
            regexes = [
                r'(Salary|Gehalt|Compensation|Vergütung):.*',
                r'\b(Gross|Brutto|Net|Netto)\b:.*',
                r'(\d{5}[.,]\d+)(?:(?!\d{5}[.,]?\d*).)*?\b(netto|brutto|gross)\b',
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
            ]
        if not method:
            method = self._salary_from_text
        return salary_from_description(text, regexes=regexes, method=method, **kwargs)

    def _salary_points(self, salary, salary_bearable=SALARY_BEARABLE, salary_ratio=0.15/100,
                      high_dropoff=True, dropoff_bearable_ratio=1.25):
        return salary_points(salary, root_value=salary_bearable, salary_ratio=salary_ratio,
                           high_dropoff=high_dropoff, dropoff_bearable_ratio=dropoff_bearable_ratio)

    def _process_posting_soups(self, soups, pattern, website="",
                              posting_id=False, posting_id_path=None,
                              posting_id_regex=r'\d+', title_path=None, 
                              company_path=None, salary_path=None):
        return process_posting_soups(soups, pattern, website=website,
                                    posting_id=posting_id, posting_id_path=posting_id_path,
                                    posting_id_regex=posting_id_regex, title_path=title_path, 
                                    company_path=company_path, salary_path=salary_path,
                                    salary_from_text_func=self._salary_from_text)

    def _save_data(self, data, path = f"{RELATIVE_POSTINGS_PATH}/", name="", with_timestamp = True, verbose = False):
        if not name:
            name = self.rules["website"]
        save_data(data, path=path, name=name, with_timestamp=with_timestamp, verbose=verbose)
    
    def _filter_postings(self, postings:dict, banned_words=None, banned_capital_words=None):
        if not banned_words:
            banned_words = self.keywords.get("banned_words", [])
        if not banned_capital_words:
            banned_capital_words = self.keywords.get("banned_capital_words", [])
        return filter_postings(postings, banned_words=banned_words,
                               banned_capital_words=banned_capital_words)
    
    def _check_locations(self, locations, locations_desired=None):
        if locations_desired is None:
            locations_desired = getattr(self, "locations_desired", LOCATIONS_DESIRED)
        return check_locations(locations=locations, locations_desired=locations_desired)

    def _rank_postings(self, postings: dict, keyword_points=None, desc_ratio=0.3,
                      salary_bearable=None, salary_ratio=0.15/100,
                      dropoff_bearable_ratio=1.4, overwrite=True,
                      locations_desired=None, locations_secodary=None, **kwargs):
        if not salary_bearable:
            salary_bearable = getattr(self, "salary_bearable", SALARY_BEARABLE)
        if not keyword_points:
            keyword_points = getattr(self, "rankings", BASE_KEYWORD_SCORING)
        if not locations_desired:
            locations_desired = getattr(self, "locations_desired", LOCATIONS_DESIRED)
        if not locations_secodary:
            locations_secodary = getattr(self, "locations_secondary", LOCATIONS_SECONDARY)

        return rank_postings(postings, keyword_points=keyword_points, desc_ratio=desc_ratio,
                           root_value=salary_bearable, salary_ratio=salary_ratio,
                           dropoff_bearable_ratio=dropoff_bearable_ratio, overwrite=overwrite,
                           locations_desired=locations_desired, locations_secodary=locations_secodary,
                           **kwargs)

    def _find_keywords(self, text, keywords_list=None, sort=False, **kwargs):
        if not keywords_list:
            keywords_list = getattr(self, "keywords", {}).get("description_keywords_order", [])
        return find_keywords(text, keywords_list=keywords_list, sort=sort, **kwargs)
    
    def _find_keywords_in_postings(self, postings: dict, ordered_keywords = None,
                                   description_key="description", overwrite=True, sort=False, **kwargs):
        if not ordered_keywords:
            ordered_keywords = getattr(self, "keywords", {}).get("description_keywords_order", [])
        return find_keywords_in_postings(postings, ordered_keywords=ordered_keywords, 
                                         description_key=description_key,
                                         method = self._find_keywords,
                                         overwrite=overwrite, sort=sort, **kwargs)

    def _apply_filters_transformations(self, postings, transformations: List[Tuple] = None):
        """
        Apply a series of transformations (e.g. on points) or filters to postings.
        """
        if transformations is None:
            transformations = getattr(self, "transformations", [])
        return apply_filters_transformations(postings, transformations=transformations)

    def _process_data(self, postings: dict, banned_words = None, banned_capital_words = None,
                     description_key="description", transformations = None, **kwargs):
        if transformations is None:
            transformations = []
        return process_data(postings = postings, banned_words=banned_words,
                            banned_capital_words=banned_capital_words,
                            filter_method=self._filter_postings,
                            language_analysis_method=analyze_postings_language,
                            rank_method=self._rank_postings,
                            keyword_finding_method=self._find_keywords_in_postings,
                            apply_filters_transformations=self._apply_filters_transformations,
                            description_key=description_key, transformations=transformations,
                            **kwargs)

    def gather_data(self, close_driver=True,
                    url_links = None,
                    posting_id = False,
                    posting_id_path = "href", #can be None
                    posting_id_regex = r'\d+',
                    titles = False,
                    companies = False,
                    salary = False,
                    description_key = "description",
                    transformations = None):
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

        if transformations is None:
            transformations = []

        if callable(url_links):
            url_links = url_links()
        if not url_links:
            url_links = self._construct_page_urls(self.rules["scraping_base_url"])

        if usecase in ["http", "https"]:
            request_wait_time = self.rules.get("request_wait_time", 0.3)
            soups = scrape.requests_responses(url_links, https=(usecase=="https"),
                                              return_kind="soups", wait_time=request_wait_time)
        elif usecase in ["selenium", "http_selenium"]:
            driver = self.driver
            if driver is None:
                if webdriver is None:
                    raise ModuleNotFoundError("selenium is required to create a webdriver")
                driver = webdriver.Firefox()
                self.driver = driver
            soups = self._load_pages(url_links, close_popup="first", close_driver=False)
        else:
            raise ValueError("Usecase not implemented")

        postings = self._process_posting_soups(soups, pattern, posting_id=posting_id, website=website,
                                      posting_id_path=posting_id_path, posting_id_regex=posting_id_regex,
                                      title_path=title_path, company_path=company_path, salary_path=salary_path)
        
        postings = self._process_data(postings, transformations=transformations, description_key=description_key)
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
        if companies:
            return postings, company_list
        return postings
