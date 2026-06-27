import re
from copy import deepcopy
from typing import List

from bs4 import BeautifulSoup

from jobscraping.config.configs import (
    BASE_KEYWORD_SCORING,
    BASE_PHRASES,
    LOCATIONS_DESIRED,
    LOCATIONS_SECONDARY,
    SALARY_BEARABLE,
)
from jobscraping.config.constants import BASE_RULES
from jobscraping.processing.attributes import (
    salary_from_description,
)
from jobscraping.scrapers import scrape
from jobscraping.scrapers.basescraper import BaseScraper
from jobscraping.scrapers.scrape import next_page_logic_by_length


class Raiffeisen(BaseScraper):
    """Scraper for Raiffeisen International postings."""
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
    
    def _next_page_logic(self, data:BeautifulSoup, pattern:str):
        return next_page_logic_by_length(data, pattern, lengths=[25,50])

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
                posting_id = re.search(r'/\d+/$', url).group().replace("/", "")
                posting_id = website + posting_id
                if posting_id not in postings:
                    title = select.text
                    if title:
                        title = title.strip()
                    postings[posting_id] = {
                        "title": title,
                        "url": url,
                        "company": "Raiffeisen International",
                        "source": website,
                        "id": posting_id,
                    }
        return postings
        
    def _clean_variables(self, variables):
        problematic_chars = ["\n", "\t", "\r", "\xa0"]
        if isinstance(variables, str):
            variables = variables.strip()
            for char in problematic_chars:
                variables = variables.replace(char, " ")
        elif isinstance(variables, list):
            for (i, variable) in enumerate(variables):
                variable = variable.strip() if variable else None
                for char in problematic_chars:
                    variable = variable.replace(char, " ") if variable else None
                variables[i] = variable
        return variables
    
    def _get_descriptions_from_soups(self, id_soup_dicts, verbose=False):
        descriptions = {}
        for posting_id, soup in id_soup_dicts.items():
            posting = soup.select("div.joblayouttoken.rtltextaligneligible.displayDTM") #TODO
            i = None
            for i in posting:
                if i.select("ul"):
                    break
            if i is None:
                if verbose:
                    print(f"Warning: No posting content found for ID {posting_id}")
                continue
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
            descriptions[posting_id] = {
                "role": role,
                "requirements": requirements,
                "salary_guessed": salary,
                "salary_monthly_guessed": salary_monthly,
                "nice_to_have": nice_to_have,
                "benefits": benefits,
                "description": description,
            }
        return descriptions

    def _salary_from_text(self, text, keywords=None,
                                               clarity_comma_char=".", decimal_separator=",", conversion_rate=14):
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

    def gather_data(self, url_links=None, descriptions=False, verbose=False,
                    transformations = None, description_key ="description"):
        titles_pattern = self.rules["gather_data_selector"]
        website = self.rules["website"]
        usecase = self.rules["usecase"]
        request_wait_time = self.rules.get("request_wait_time", 0.16)
        more_pages_url_extension = self.rules["more_pages_url_extension"]
        jobs_base_url = self.rules["jobs_base_url"]

        if transformations is None:
            transformations = []
        if not url_links:
            url_links = self._construct_page_urls(self.rules["scraping_base_url"])

        postings = {}
        def _add_matched_titleword(posting_data, titleword):
            if not titleword:
                return
            matched = posting_data.get("matched_titlewords")
            if not matched:
                posting_data["matched_titlewords"] = [titleword]
            elif titleword not in matched:
                matched.append(titleword)

        def _titleword_from_url(url):
            base_url = self.rules["scraping_base_url"]
            if url.startswith(base_url):
                return url[len(base_url):].split("&")[0]
            return None

        def _add_postings_from_soup(soup, matched_titleword):
            selects = soup.select(titles_pattern)
            for select in selects:
                title = select.text
                url = jobs_base_url + select["href"]
                posting_id = re.search(r'/\d+/$', url).group().replace("/", "")
                posting_id = website + posting_id
                if posting_id not in postings:
                    if title:
                        title = title.strip()
                    postings[posting_id] = {
                        "title": title,
                        "url": url,
                        "company": "Raiffeisen International",
                        "source": website,
                        "id": posting_id,
                        "matched_titlewords": [matched_titleword] if matched_titleword else [],
                    }
                else:
                    _add_matched_titleword(postings[posting_id], matched_titleword)

        for url in url_links:
            matched_titleword = _titleword_from_url(url)
            result = scrape.requests_responses([url], https=(usecase=="https"),
                                              return_kind="soups", wait_time=request_wait_time,
                                              verbose=verbose)
            if not result:
                if verbose:
                    print(f"No response received for {url}, skipping...")
                continue
            soup = result[0]
            _add_postings_from_soup(soup, matched_titleword)
            row = 25
            get_next_page = self._next_page_logic(soup, titles_pattern)
            while get_next_page:
                if verbose:
                    print(f"Getting next page for {url}")
                next_page = url + more_pages_url_extension + str(row)
                result = scrape.requests_responses([next_page], https=(usecase=="https"),
                                                  return_kind="soups", wait_time=request_wait_time,
                                                  verbose=verbose)
                if not result:
                    if verbose:
                        print(f"No response for next page {next_page}, stopping pagination...")
                    break
                soup = result[0]
                _add_postings_from_soup(soup, matched_titleword)
                get_next_page = self._next_page_logic(soup, titles_pattern)
                row += 25

        postings = self._filter_postings(postings)

        if descriptions:
            url_list = [posting["url"] for posting in postings.values()]
            ids = [website+re.search(r'/\d+/$', url).group().replace("/", "") for url in url_list]
            soups = scrape.requests_responses(url_list, https=(usecase=="https"),
                                              return_kind="soups", wait_time=request_wait_time,
                                              verbose=verbose)
            #Match ids to soups (if some requests failed, soups may be shorter)
            ids_soups = dict(zip(ids[:len(soups)], soups))
            descriptions = self._get_descriptions_from_soups(ids_soups, verbose=verbose)
            for _id, posting in descriptions.items():
                postings[_id] = {'id':_id, 'title':postings[_id]["title"],
                                'company':postings[_id]["company"],
                                **posting, 'url':postings[_id]["url"],
                                'source':postings[_id]["source"],
                                "collected_on": self.business_day,
                                }
        
        postings = self._process_data(postings, transformations=transformations, description_key=description_key)
        return postings
