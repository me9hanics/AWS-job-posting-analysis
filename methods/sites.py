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
                   "data science", "data scientist", "data mining",
                   "data engineer", "data engineering", "data engineering developer",
                   "data analysis", "data analytics", "data analyst",
                   "graph theory", "network science", "graph database",
                   "business intelligence", "business intelligence analyst", "bi analyst", "business analyst",
                   #"complexity science",
                  ],
    "titlewords_dashed": ["machine-learning","machine-learning-engineer","machine-learning-scientist",
                          "ML-scientist", "ML-engineer", "ML-researcher", "ML-developer", "ML-AI",
                          "AI-engineer", "AI-scientist", "AI-researcher", "AI-developer", "AI-ML", 
                          "data-science","data-scientist", "data-mining",
                          "data-engineer", "data-engineering", "data-engineering-developer",
                          "data-analysis", "data-analytics", "data-analyst",
                          "graph-theory", "network-science", "graph-database",
                          "business-intelligence", "business-intelligence-analyst", "bi-analyst", "business-analyst",
                          #"complexity-science",
                          ],
    "banned_words": ["manager", "management", "professor", "team leader", "teamleader", "teamleiter", "team leiter",
                    "jurist", "lawyer", "audit", "legal", "advisor", "owner", "officer", "controller", "cyber security"
                    "praktikum", "praktikant", #"internship", "intern", "trainee",
                    ],
    "banned_capital_words": ["SAP", "HR"],
}

class BaseScraper:
    def __init__(self, driver=None, rules = BASE_RULES, keywords = BASE_KEYWORDS):
        if driver is None:
            self.driver = webdriver.Firefox()
        else:
            self.driver = driver
        self.rules = rules
        self.keywords = keywords

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

    def construct_page_urls(self, base_url = None):
        if base_url is None:
            base_url = self.rules["scraping_base_url"]
        locations = self.keywords["locations"]
        titlewords = self.keywords["titlewords"]
        links = urls.urls_builder(base_url = base_url, slash_elements_list = [titlewords, locations],
                                  zipped = True, all_combinations = True)
        links = list(set(links)) #Don't include duplicates
        return links

    def salary_number_from_str(self, text, keywords=[],
                               remove_chars = ['.'], lengths=[6,5]):
        if type(text) != str:
            return None
        for char in remove_chars:
            text = text.replace(char, "")
        if not keywords:
            for length in lengths:
                #Search for length-digit numbers
                value = re.search(rf'\d{{{length}}}', text)
                if value:
                    return int(value.group())
        else:
            if any([keyword in text for keyword in keywords]):
                for length in lengths:
                    value = re.search(rf'\d{{{length}}}', text)
                    if value:
                        return int(value.group())
        return None
    
    def salary_regex(self, text, regexes=[r'\d{6},\d{2}', r'\d{5},\d{2}',  r'\d{6}', r'\d{5}']):
        for regex in regexes:
            value = re.search(regex, text)
            if value:
                try:
                    return int(value.group())
                except ValueError:
                    return int(float(value.group().replace(",",".")))
        return None

    def salary_from_text(self, text, keywords={"annual":["jährlich", "yearly", "per year", "annual", "jährige", "pro jahr"],
                                               "monthly":["monatlich", "monthly", "per month", "pro monat"]},
                                               clarity_comma_char=".", conversion_rate=14):
        if type(text) != str:
            return None
        text = text.lower()
        salary = {}
        if "annual" in keywords.keys():
            value = self.salary_number_from_str(text, keywords["annual"], remove_chars=[clarity_comma_char], lengths=[6,5])
            if value:
                salary["annual"] = value
        if (not salary) and ("monthly" in keywords.keys()):
            value = self.salary_regex(text.replace(clarity_comma_char, ""), regexes=[r'\d{4},\d{2}'])
            if not value:
                value = self.salary_number_from_str(text, keywords["monthly"], remove_chars=[clarity_comma_char], lengths=[4])
            if value:
                salary["monthly"] = value
        if not salary:
            value = self.salary_regex(text.replace(clarity_comma_char, ""),
                                      regexes=[r'\d{6},\d{2}', r'\d{5},\d{2}',  r'\d{6}', r'\d{5}'])
            if value:
                salary["annual"] = value
            else:
                value = self.salary_regex(text.replace(clarity_comma_char, ""), regexes=[r'\d{4},\d{2}', r'\d{4}'])
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

    def process_soups(self, soups, pattern, website = "",
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
    
    def filter_postings(self, postings:dict, banned_words=[], banned_capital_words=[]):
        if not banned_words:
            banned_words = self.keywords["banned_words"]
        if not banned_capital_words:
            banned_capital_words = self.keywords["banned_capital_words"]
        filtered_postings = {}
        for id, posting in postings.items():
            title = posting["title"]
            if any([word in title.lower() for word in banned_words]):
                continue
            if any([word in title for word in banned_capital_words]):
                continue
            filtered_postings[id] = posting
        return filtered_postings
        
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
            soups = scrape.requests_responses(url_links, https=True if usecase=="https" else False, wait_time=request_wait_time)
        elif usecase in ["selenium", "http_selenium"]:
            driver = self.driver
            if driver is None:
                driver = webdriver.Firefox()
            soups = self.load_pages(url_links, close_popup="first", close_driver=False)
        else:
            raise ValueError("Usecase not implemented")

        postings = self.process_soups(soups, pattern, posting_id=posting_id, website=website,
                                      posting_id_path=posting_id_path, posting_id_regex=posting_id_regex,
                                      title_path=title_path, company_path=company_path, salary_path=salary_path)
        
        postings = self.filter_postings(postings)
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
    def __init__(self, driver="", rules = BASE_RULES, keywords = BASE_KEYWORDS):
        """
        If Selenium is used, the driver argument should be None or a previously opened driver
        If it is not used, the driver argument should be something other than None
        """
        rules["website"] = "karriere.at"
        rules["usecase"] = "selenium"
        rules["scraping_base_url"] = "https://www.karriere.at/jobs"
        rules["request_wait_time"] = 0.16
        if driver or type(driver) == type(None):
            keywords["locations"] = ["wien-und-umgebung"]
            keywords["titlewords"] = keywords["titlewords_dashed"]
        else:
            keywords["locations"] = ["wien und umgebung"]
        super().__init__(driver, rules, keywords)
        
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
    
    def gather_data(self, close_driver=True, descriptions=False, save_data=False, verbose=False):
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
                                           "X-CSRF-Token": "GVJiHEzc3AZ3syhOq8TV1DpRECCEvAnDIzJ3hGSW",
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
                                           "X-CSRF-Token": "GVJiHEzc3AZ3syhOq8TV1DpRECCEvAnDIzJ3hGSW",
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
                        postings[id]["description"] = posting
                    else:
                        if verbose:
                            print(f"Could not find posting with id {id}")

        if save_data:
            self.save_data(postings, name=f"karriere_at", with_date=True)
        return postings