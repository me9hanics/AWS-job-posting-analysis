import requests
from bs4 import BeautifulSoup
import re
import time
import json
import os
from copy import deepcopy
from typing import List, Tuple, Callable
try:
    from methods import scrape
    from methods import urls
    from methods.macros import (SALARY_BEARABLE, BASE_RULES, BASE_KEYWORDS, BASE_KEYWORD_SCORING,
                                RELATIVE_POSTINGS_PATH, LOCATIONS_DESIRED, LOCATIONS_SECONDARY) 
    from methods.attributes import *
    from methods.postings_utils import (filter_postings, process_posting_soups)
    from methods.transformations import apply_filters_transformations
    from methods.files_io import save_data
    from methods.scrape import next_page_logic_by_length
except ModuleNotFoundError:
    import scrape
    import urls
    from macros import (SALARY_BEARABLE, BASE_RULES, BASE_KEYWORDS, BASE_KEYWORD_SCORING,
                        RELATIVE_POSTINGS_PATH, LOCATIONS_DESIRED, LOCATIONS_SECONDARY)
    from attributes import *
    from postings_utils import (filter_postings, process_posting_soups)
    from transformations import apply_filters_transformations
    from files_io import save_data
    from scrape import next_page_logic_by_length

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, TimeoutException

GET_HEIGHT_SCRIPT = "return document.body.scrollHeight"
SCROLL_DOWN_SCRIPT = "window.scrollTo(0, document.body.scrollHeight);" #scroll to height value of the bottom of the page
SCROLL_1000_SCRIPT = "window.scrollTo(0, 1000);"
CSS_SELECTOR = "css selector" #can use instead: from selenium.webdriver.common.by import By, then By.CSS_SELECTOR

def get_all_keywords(keywords = BASE_KEYWORDS, #rankings = BASE_KEYWORD_SCORING
                     ):
    """
    Returns union of keywords (as lists), non capitalized and capitalized.
    """
    
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
#ALL_KEYWORDS_NONCAPITAL, ALL_KEYWORDS_CAPITAL = get_all_keywords(keywords=BASE_KEYWORDS)


class BaseScraper:
    def __init__(self, driver=None, rules = BASE_RULES, keywords = BASE_KEYWORDS,
                 extra_keywords = {}, extra_titlewords = [], extra_locations = [],
                 rankings = BASE_KEYWORD_SCORING, salary_bearable = SALARY_BEARABLE, locations = None,
                 locations_desired = LOCATIONS_DESIRED, locations_secondary = LOCATIONS_SECONDARY,
                 transformations = []):
        if driver is None:
            self.driver = webdriver.Firefox()
        else:
            self.driver = driver

        self.time = time.strftime("%Y-%m-%d-%H-%M-%S")
        self.day = self.time[:10]

        #rules = rules or BASE_RULES
        self.rules = rules
        self.BASE_RULES = rules

        self.keywords = deepcopy(keywords)
        if extra_keywords:
            for key_type, key_values in extra_keywords.items():
                self.keywords[key_type] = list(set(self.keywords.get(key_type, []) + key_values))
        if extra_titlewords:
            self.keywords["titlewords"] = list(set(self.keywords.get("titlewords", []) + extra_titlewords))
        locations = locations if locations else keywords.get("locations", LOCATIONS_DESIRED)
        if extra_locations:
            locations = list(set(locations + extra_locations))
        self.keywords["locations"] = locations
        self.BASE_KEYWORDS = deepcopy(self.keywords)

        #TODO same with rankings
        self.rankings = rankings
        self.BASE_RANKINGS = rankings
        #self.signed_rankings = rankings.get("ranking_case_sensitive", {}).copy().update(rankings.get("ranking_lowercase", {}))
        
        self.all_keywords = self.keywords.get("description_keywords_order", [])
        self.description_keywords_order = self.keywords.get("description_keywords_order", [])

        self.salary_bearable = salary_bearable

        self.locations = locations
        self.locations_desired = locations_desired
        self.locations_secondary = locations_secondary

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

    def _load_pages(self, urls, close_popup="first", popup_closing_wait=12.0,
                   page_load_method: Callable = None,
                   load_more_button = True, load_by_scrolling = False,
                   post_click_wait = 0.0, close_driver=True, **kwargs):
        driver = self.driver
        if not page_load_method:
            page_load_method = getattr(self, "page_load_method", None) or self._load_page
        return scrape.load_pages(driver, urls, close_popup=close_popup, popup_closing_wait=popup_closing_wait,
                                page_load_method=page_load_method,
                                load_more_button = load_more_button, load_by_scrolling = load_by_scrolling,
                                post_click_wait = post_click_wait, close_driver=close_driver, **kwargs)

    def next_page_logic(self, input, **kwargs):
        """input: typically a soup or HTML element, possibly dict or string"""
        #TODO
        pass

    def _salary_from_text(self, text, keywords={"annual":["jährlich", "yearly", "per year", "annual", "jährige", "pro jahr", "p.a."],
                                               "monthly":["monatlich", "monthly", "per month", "pro monat"]},
                                               clarity_comma_char=".", decimal_separator=",", conversion_rate=12):
        return salary_from_text(text, keywords=keywords, clarity_comma_char=clarity_comma_char,
                                decimal_separator=decimal_separator, conversion_rate=conversion_rate)

    def _salary_from_description(self, text,
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
                                 method : Callable = None,
                                 **kwargs):
        if type(text) != str:
            return None
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
    
    def _check_locations(self, locations, locations_desired=["vienna", "wien", "österreich"]):
        if not locations_desired:
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

    def _apply_filters_transformations(self, postings, transformations: List[Tuple] = []):
        """
        Apply a series of transformations (e.g. on points) or filters to postings.
        """
        if not transformations:
            transformations = getattr(self, "transformations", [])
        return apply_filters_transformations(postings, transformations=transformations)

    def gather_data(self, close_driver=True,
                    url_links = [],
                    posting_id = False,
                    posting_id_path = "href", #can be None
                    posting_id_regex = r'\d+',
                    titles = False,
                    companies = False,
                    salary = False,
                    transformations = []):
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
            url_links = self._construct_page_urls(self.rules["scraping_base_url"])

        if usecase in ["http", "https"]:
            request_wait_time = self.rules["request_wait_time"] if "request_wait_time" in self.rules.keys() else 0.3
            soups = scrape.requests_responses(url_links, https=True if usecase=="https" else False,
                                              return_kind="soups", wait_time=request_wait_time)
        elif usecase in ["selenium", "http_selenium"]:
            driver = self.driver
            if driver is None:
                driver = webdriver.Firefox()
            soups = self._load_pages(url_links, close_popup="first", close_driver=False)
        else:
            raise ValueError("Usecase not implemented")

        postings = self._process_posting_soups(soups, pattern, posting_id=posting_id, website=website,
                                      posting_id_path=posting_id_path, posting_id_regex=posting_id_regex,
                                      title_path=title_path, company_path=company_path, salary_path=salary_path)
        
        postings = self._filter_postings(postings)
        postings = analyze_postings_language(postings)
        postings = self._rank_postings(postings)
        postings = self._find_keywords_in_postings(postings)
        postings = self._apply_filters_transformations(postings, transformations=transformations)
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


class KarriereAT(BaseScraper):
    def __init__(self, driver="", rules = BASE_RULES, keywords = BASE_KEYWORDS,
                 extra_keywords = {}, extra_titlewords = [], extra_locations = [],
                 rankings = BASE_KEYWORD_SCORING, salary_bearable = SALARY_BEARABLE, locations = None,
                 locations_desired = LOCATIONS_DESIRED, locations_secondary = LOCATIONS_SECONDARY,
                 transformations = []):
        """
        If Selenium is used, the driver argument should be None or a previously opened driver
        If it is not used, the driver argument should be something other than None
        """
        rules["website"] = "karriere.at"
        rules["scraping_base_url"] = "https://www.karriere.at/jobs"
        rules["usecase"] = "https"
        rules["close_website_popup"] = False
        rules["load_page_button_selector"] = ".onetrust-close-btn-handler"
        rules["load_page_press_button_until_gone_selector"] = ".m-loadMoreJobsButton__button"
        rules["gather_data_selector"] = 'div.m-jobsListItem__container div.m-jobsListItem__dataContainer h2.m-jobsListItem__title a.m-jobsListItem__titleLink'
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
                         extra_keywords = extra_keywords, extra_titlewords=extra_titlewords,
                         extra_locations=extra_locations, salary_bearable=salary_bearable, locations=locations,
                         locations_desired=locations_desired, locations_secondary=locations_secondary,
                         transformations = transformations)
        
    def _load_job(self, url, close_popup=False,
                 popup_wait=5.0, post_click_wait=1.0,
                 close_driver=True, return_url=False):
        """ Warning: outdated method """
        popup_selector = self.rules["load_page_button_selector"]
        driver = self.driver
        if driver is None:
            driver = webdriver.Firefox()
        driver.get(url)
        
        if close_popup:
            soup = self._close_website_popup(popup_selector, url = url, click_wait=popup_wait,
                                            post_click_wait=post_click_wait, post_click_scroll_down=True,
                                            close_driver=False, open_page=False)
        if close_driver:
            driver.quit()

        if return_url:
            return soup, url
        return soup

    def _load_jobs(self, urls, close_popup=False,
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
                soup, url = self._load_job(url, close_popup=close_popup, 
                                          popup_wait=popup_wait, post_click_wait=post_click_wait, 
                                          close_driver=False, return_url=True)
                links.append(url)
            else:
                soup = self._load_job(url, driver=driver, close_popup=close_popup, 
                                     popup_wait=popup_wait, post_click_wait=post_click_wait, 
                                     close_driver=False, return_url=False)
            soups.append(soup)

        if close_driver:
            driver.quit()

        if return_urls:
            return soups, links
        return soups

    def _load_page(self, url, close_popup=True,
                  popup_wait=12.0, pre_click_scroll=True,
                  post_popup_close_wait=0.3,
                  first_load_more_wait = 0.1, post_load_more_wait=0.1,
                  close_driver=True, **kwargs):
        """ Warning: Outdated method """

        popup_selector = self.rules["load_page_button_selector"]
        load_more_selector = self.rules["load_page_press_button_until_gone_selector"]
        final_page_soup = super()._load_page(url, close_popup=close_popup,
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

    def _data_gather_outdated_selenium(self, close_driver=True,
                    descriptions = False):
        """ Warning: outdated method """

        pattern = self.rules["gather_data_selector"]
        website = self.rules["website"]
        #usecase = self.rules["usecase"]
        #title_path = self.rules["title_path"]
        #company_path = self.rules["company_path"]
        if driver is None:
            driver = webdriver.Firefox()
        links = self._construct_page_urls()
        soups = self._load_pages(links, close_popup="first", close_driver=False)

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
            soups,returned_urls = self._load_jobs(jobs_url, popup_wait=2.2, close_driver=False, return_urls=True)
            ids = [re.search(r'\d+', url).group() for url in returned_urls]

            for i,soup in enumerate(soups):
                description = soup.find("div", class_="m-jobContent__jobText m-jobContent__jobText--standalone")
                if description:
                    description = description.text.strip()
                postings[ids[i]]["description"] = description

        if close_driver:
            driver.quit()
        return postings

    def _salary_from_text(self, text, keywords={"annual":["jährlich", "yearly", "per year", "annual", "jährige", "pro jahr", "p.a."],
                                               "monthly":["monatlich", "monthly", "per month", "pro monat"]},
                                               clarity_comma_char=".", decimal_separator=",", conversion_rate=14):
        #Conversion rate is 14 here as in Austria 14 salaries are paid per year
        return super()._salary_from_text(text, keywords=keywords, clarity_comma_char=clarity_comma_char,
                                        decimal_separator=decimal_separator, conversion_rate=conversion_rate)
        
    def gather_data(self, descriptions=False, save_data=False, verbose=False, transformations = []):
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
                            salary_read = self._salary_from_text(posting['salary'])
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

        postings = self._filter_postings(postings)

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
                postings = self._find_keywords_in_postings(postings)

        postings = self._rank_postings(postings)
        postings = {k: v for k, v in sorted(postings.items(), key=lambda item: item[1]["points"], reverse=True)}
        postings = self._apply_filters_transformations(postings, transformations=transformations)
        if save_data:
            self._save_data(postings, name=f"karriere_at", with_timestamp=True)
        return postings
    
class Raiffeisen(BaseScraper):
    def __init__(self, driver="", rules = BASE_RULES, keywords = BASE_KEYWORDS,
                 extra_keywords = {}, extra_titlewords = [], extra_locations = [],
                 rankings = BASE_KEYWORD_SCORING, salary_bearable = SALARY_BEARABLE, locations = None,
                 locations_desired=LOCATIONS_DESIRED, locations_secondary=LOCATIONS_SECONDARY,
                 transformations = []):
        rules["website"] = "raiffeisen_international"
        rules["scraping_base_url"] = "https://jobs.rbinternational.com/search/?q="
        rules["jobs_base_url"] = "https://jobs.rbinternational.com"
        rules["usecase"] = "http"
        rules['gather_data_selector'] = 'a.jobTitle-link'
        rules['more_pages_url_extension'] = "&sortColumn=referencedate&sortDirection=desc&startrow="
        rules['description_selector'] = 'ul'
        rules["request_wait_time"] = 0.3 if "request_wait_time" not in rules.keys() else rules["request_wait_time"]
        
        for key, value in BASE_RULES.items():
            if key not in rules.keys():
                rules[key] = value

        if not keywords:
            keywords = deepcopy(BASE_KEYWORDS)
        
        super().__init__(driver=driver, rules=rules, keywords=keywords, rankings=rankings,
                         extra_keywords = extra_keywords, extra_titlewords=extra_titlewords,
                         extra_locations=extra_locations, salary_bearable=salary_bearable, locations=locations,
                         locations_desired=locations_desired, locations_secondary=locations_secondary, 
                         transformations = transformations)

    def _construct_page_urls(self, base_url = None, titlewords = None):
        if base_url is None:
            base_url = self.rules["scraping_base_url"]
        if titlewords is None:
            titlewords = self.keywords["titlewords"]
        links = []
        for titleword in titlewords:
            links.append(base_url + titleword)
        links = list(set(links)) #Don't include duplicates
        return links
    
    def _next_page_logic(self, input:BeautifulSoup, pattern:str):
        return next_page_logic_by_length(input, pattern, lengths=[25,50])

    def _process_posting_soups(self, soups:List[BeautifulSoup], pattern:str,
                              website="", jobs_base_url=None):
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
        
    def _clean_variables(self, variables):
        problematic_chars = ["\n", "\t", "\r", "\xa0"]
        if type(variables) == str:
            variables = variables.strip()
            for char in problematic_chars:
                variables = variables.replace(char, " ")
        elif type(variables) == list:
            for (i, variable) in enumerate(variables):
                variable = variable.strip() if variable else None
                for char in problematic_chars:
                    variable = variable.replace(char, " ") if variable else None
                variables[i] = variable
        return variables
    
    def _get_descriptions_from_soups(self, id_soup_dicts, verbose=False):
        descriptions = {}
        for id, soup in id_soup_dicts.items():
            posting = soup.select("div.joblayouttoken.rtltextaligneligible.displayDTM") #TODO
            for i in posting:
                if i.select("ul"):
                    break
            posting = i
            contexts = posting.select("ul")
            contexts = [context for context in contexts if context.attrs == {}]
            if len(contexts) not in [3, 4]:
                if verbose:
                    #print(f"Contexts length not 4, but {len(contexts)}; something incorrect. Contexts: {contexts}")
                    pass

            role = contexts[0].text if contexts else None
            requirements = contexts[1].text if len(contexts) > 1 else None
            benefits = contexts[2].text if len(contexts) > 2 else None
            nice_to_have = None

            if len(contexts) == 3:
                benefits = contexts[2].text
            elif len(contexts) == 4:
                nice_to_have = contexts[2].text
                benefits = contexts[3].text
            elif len(contexts) > 4:
                benefits = "\n ".join([context.text for context in contexts[2:]])

            description = posting.text
            salary = None
            salary_monthly = None
            if benefits:
                salary = salary_from_description(benefits, decimal_separator=".", clarity_comma_char=",")
                if not salary:
                    salary = salary_from_description(benefits, decimal_separator=",", clarity_comma_char=".")
                salary_monthly = salary["monthly"] if salary else None

            role, requirements, nice_to_have, benefits, description = self._clean_variables([role, requirements, nice_to_have, benefits, description])
            descriptions[id] = {"role": role, "requirements": requirements,
                                "salary_guessed": salary, "salary_monthly_guessed": salary_monthly,
                                "nice_to_have": nice_to_have, "benefits": benefits,
                                "description": description}
        return descriptions

    def _salary_from_text(self, text, keywords={"annual":["jährlich", "yearly", "per year", "annual", "jährige", "pro jahr", "p.a."],
                                               "monthly":["monatlich", "monthly", "per month", "pro monat"]},
                                               clarity_comma_char=".", decimal_separator=",", conversion_rate=14):
        #Conversion rate is 14 here as in Austria 14 salaries are paid per year
        return super()._salary_from_text(text, keywords=keywords, clarity_comma_char=clarity_comma_char,
                                        decimal_separator=decimal_separator, conversion_rate=conversion_rate)

    def gather_data(self, url_links=[], descriptions=False, verbose=False, transformations = []):
        titles_pattern = self.rules["gather_data_selector"]
        website = self.rules["website"]
        usecase = self.rules["usecase"]
        request_wait_time = self.rules["request_wait_time"] if "request_wait_time" in self.rules.keys() else 0.16
        more_pages_url_extension = self.rules["more_pages_url_extension"]
        jobs_base_url = self.rules["jobs_base_url"]


        if url_links == []:
            url_links = self._construct_page_urls(self.rules["scraping_base_url"])

        soups = []
        for url in url_links:
            soup = scrape.requests_responses([url], https=True if usecase=="https" else False,
                                              return_kind="soups", wait_time=request_wait_time)[0]
            soups.append(soup)
            row = 25
            get_next_page = self._next_page_logic(soup, titles_pattern)
            while get_next_page:
                if verbose:
                    print(f"Getting next page for {url}")
                next_page = url + more_pages_url_extension + str(row)
                soup = scrape.requests_responses([next_page], https=True if usecase=="https" else False,
                                                  return_kind="soups", wait_time=request_wait_time)[0]
                soups.append(soup)
                get_next_page = self._next_page_logic(soup, titles_pattern)
                row += 25
                
        postings = self._process_posting_soups(soups, titles_pattern, website=website,
                                      jobs_base_url=jobs_base_url)
        postings = self._filter_postings(postings)

        if descriptions:
            urls = [posting["url"] for posting in postings.values()]
            ids = [website+re.search(r'/\d+/$', url).group().replace("/", "") for url in urls]
            soups = scrape.requests_responses(urls, https=True if usecase=="https" else False,
                                              return_kind="soups", wait_time=request_wait_time)
            ids_soups = {id:soup for id,soup in zip(ids, soups)}
            descriptions = self._get_descriptions_from_soups(ids_soups, verbose=verbose)
            for id, posting in descriptions.items():
                postings[id] = {'id':id, 'title':postings[id]["title"],
                                'company':postings[id]["company"],
                                **posting, 'url':postings[id]["url"],
                                'source':postings[id]["source"],
                                "collected_on": self.day,
                                }
        
        postings = self._rank_postings(postings)
        postings = self._find_keywords_in_postings(postings)
        postings = self._apply_filters_transformations(postings, transformations=transformations)
        return postings