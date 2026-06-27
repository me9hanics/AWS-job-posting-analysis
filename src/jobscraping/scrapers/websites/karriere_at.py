import json
import re
from copy import deepcopy

from bs4 import BeautifulSoup

try:
    from selenium import webdriver
except ModuleNotFoundError:
    webdriver = None
from jobscraping.config.configs import (
    BASE_KEYWORD_SCORING,
    BASE_PHRASES,
    LOCATIONS_DESIRED,
    LOCATIONS_SECONDARY,
    SALARY_BEARABLE,
)
from jobscraping.config.constants import BASE_RULES
from jobscraping.scrapers import scrape
from jobscraping.scrapers.basescraper import BaseScraper


class KarriereAT(BaseScraper):
    """Scraper for karriere.at postings."""
    def __init__(
        self,
        driver="",
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
        """
        If Selenium is used, the driver argument should be None or a previously opened driver
        If it is not used, the driver argument should be something other than None
        """
        if rules is None:
            rules = deepcopy(BASE_RULES)
        else:
            rules = deepcopy(rules)

        if keywords is None:
            keywords = deepcopy(BASE_PHRASES)
        else:
            keywords = deepcopy(keywords)

        if extra_keywords is None:
            extra_keywords = {}
        if extra_titlewords is None:
            extra_titlewords = []
        if extra_locations is None:
            extra_locations = []
        if rankings is None:
            rankings = deepcopy(BASE_KEYWORD_SCORING)
        if transformations is None:
            transformations = []
        if locations_desired is None:
            locations_desired = list(LOCATIONS_DESIRED)
        if locations_secondary is None:
            locations_secondary = list(LOCATIONS_SECONDARY)
        rules["website"] = "karriere.at"
        rules["scraping_base_url"] = "https://www.karriere.at/jobs"
        rules["usecase"] = "https"
        rules["close_website_popup"] = False
        rules["load_page_button_selector"] = ".onetrust-close-btn-handler"
        rules["load_page_press_button_until_gone_selector"] = ".m-loadMoreJobsButton__button"
        rules["gather_data_selector"] = 'div.m-jobsListItem__container div.m-jobsListItem__dataContainer h2.m-jobsListItem__title a.m-jobsListItem__titleLink'
        rules["request_wait_time"] = 0.16
        if driver is None or driver:
            keywords["locations"] = ["wien-und-umgebung"]
            locations = ["wien-und-umgebung"]
            #keywords["titlewords"] = keywords["titlewords_dashed"]
        else:
            keywords["locations"] = ["wien und umgebung"]
            locations = ["wien und umgebung"]

        self.csrf_token = "GVJiHEzc3AZ3syhOq8TV1DpRECCEvAnDIzJ3hGSW"
        super().__init__(driver=driver, rules=rules, keywords=keywords, rankings=rankings,
                 extra_keywords = extra_keywords, extra_titlewords=extra_titlewords,
                 extra_locations=extra_locations, salary_bearable=salary_bearable,
                 locations=locations, locations_desired=locations_desired,
                 locations_secondary=locations_secondary,
                 transformations = transformations)

    def _salary_from_text(self, text, keywords=None, clarity_comma_char=".",
                          decimal_separator=",", conversion_rate=14):
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
        #Conversion rate is 14 here as in Austria 14 salaries are paid per year
        return super()._salary_from_text(text, keywords=keywords, clarity_comma_char=clarity_comma_char,
                                        decimal_separator=decimal_separator, conversion_rate=conversion_rate)
        
    def gather_data(self, descriptions=False, save_data=False, verbose=False,
                    transformations = None, description_key="description"):
        website = self.rules["website"]
        locations = self.keywords["locations"]
        titlewords = self.keywords["titlewords"] #expected not to have dashes, but spaces
        wait_time = self.rules["request_wait_time"]
        if transformations is None:
            transformations = []
        pairs = [(title, location) for title in titlewords for location in locations]
        postings = {}
        def _add_matched_titleword(posting_data, titleword):
            if not titleword:
                return
            matched = posting_data.get("matched_titlewords")
            if not matched:
                posting_data["matched_titlewords"] = [titleword]
            elif titleword not in matched:
                matched.append(titleword)
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
                                           "X-CSRF-Token": self.csrf_token,
                                           "X-Requested-With": "XMLHttpRequest",
                                       },
                                       return_kind='responses',
                                       verbose=verbose)
            if responses:
                for response in responses:
                    content = json.loads(response.text)
                    items = content['data']['jobsSearchList']['activeItems']['items']
                    for _, item in enumerate(items):
                        if 'jobsItem' in item:
                            posting = item['jobsItem']
                            locs = posting['locations']
                            salary_read = self._salary_from_text(posting['salary'])
                            posting_id = website + str(posting['id'])
                            if posting_id not in postings:
                                postings[posting_id] = {
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
                                    "collected_on": self.business_day,
                                    "date": posting['date'],
                                    "id": posting['id'],
                                    "matched_titlewords": [pair[0]] if pair[0] else [],
                                }
                            else:
                                _add_matched_titleword(postings[posting_id], pair[0])
                        else:
                            if ('alarmDisruptor' not in item) and ('contentAd' not in item) and ('bsAd' not in item):
                                if verbose:
                                    print(item)
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
                                           "X-CSRF-Token": self.csrf_token,
                                           "X-Requested-With": "XMLHttpRequest",
                                       },
                                       return_kind='responses',
                                       verbose=verbose)
            if responses:
                for response in responses:
                    content = json.loads(response.text)
                    posting = content['data']['jobDetailContent']['jobContent']['text']
                    _id = content['data']['jobDetailContent']['jobHeader']['job']['id']
                    _id = website+str(_id)
                    if _id in postings:
                        if posting:
                            posting = BeautifulSoup(posting, 'html.parser').get_text()
                            postings[_id]["description"] = posting
                    else:
                        if verbose:
                            print(f"Could not find id {_id} in saved postings - likely programming error")
                postings = self._find_keywords_in_postings(postings)

        postings = self._process_data(postings, transformations=transformations, description_key=description_key)
        if save_data:
            self._save_data(postings, name="karriere_at", with_timestamp=True)
        return postings
