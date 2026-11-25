"""Raiffeisen International scraper, its parsers and its declared steps."""

import re
from copy import deepcopy
from types import SimpleNamespace

from jobscraping.config.configs import (
    BASE_KEYWORD_SCORING,
    BASE_PHRASES,
    LOCATIONS_DESIRED,
    LOCATIONS_SECONDARY,
    SALARY_BEARABLE,
)
from jobscraping.config.constants import BASE_RULES
from jobscraping.processing.attributes import (
    add_matched_titleword,
    salary_from_description,
)
from jobscraping.processing.postings_utils import (
    factual_postings,
    split_cached_postings,
)
from jobscraping.scrapers import http, pagination
from jobscraping.scrapers.basescraper import BaseScraper
from jobscraping.scrapers.steps import RecordSet, Step
from jobscraping.specs.postings import COLLECTED_POSTINGS, DISCOVERED_POSTINGS


def page_urls(titlewords, base_url) -> list[str]:
    """One search URL per title word, without duplicates."""
    links = [base_url + titleword for titleword in titlewords]
    return list(set(links))


def parse_listing_soups(soups, titles_pattern, website, jobs_base_url) -> RecordSet:
    """Identity, URL and title for every listing link in the given soups."""
    postings = {}
    for soup in soups:
        for select in soup.select(titles_pattern):
            title = select.text
            url = jobs_base_url + select["href"]
            id_match = re.search(r'/\d+/$', url)
            if not id_match:
                continue
            posting_id = website + id_match.group().replace("/", "")
            if posting_id not in postings:
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


def has_next_page(soup, titles_pattern) -> bool:
    """The site lists in blocks of 25, so a full block may have a successor."""
    return pagination.next_page_logic_by_length(soup, titles_pattern, lengths=[25, 50])


def clean_variables(variables):
    """Replace the site's layout whitespace with single spaces."""
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


def parse_detail_soups(id_soup_dicts, verbose=False) -> dict:
    """Description sections for each posting id, keyed by posting id."""
    descriptions = {}
    for posting_id, soup in id_soup_dicts.items():
        posting = soup.select("div.joblayouttoken.rtltextaligneligible.displayDTM")
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

        role, requirements, nice_to_have, benefits, description = clean_variables(
            [role, requirements, nice_to_have, benefits, description]
        )
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


class Raiffeisen(BaseScraper):
    """Scraper for Raiffeisen International postings."""

    source = "raiffeisen_international"

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
        date_day=None,
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
        if "request_wait_time" not in rules:
            rules["request_wait_time"] = 0.3

        for key, value in BASE_RULES.items():
            if key not in rules:
                rules[key] = value

        super().__init__(driver=driver, rules=rules, keywords=keywords, rankings=rankings,
                         extra_keywords = extra_keywords, extra_titlewords=extra_titlewords,
                         extra_locations=extra_locations, salary_bearable=salary_bearable, locations=locations,
                         locations_desired=locations_desired, locations_secondary=locations_secondary, 
                         transformations = transformations, date_day=date_day)
        self.steps = (
            Step("listings", self.listings, output_spec=DISCOVERED_POSTINGS),
            Step("details", self.details, input_spec=DISCOVERED_POSTINGS,
                 output_spec=COLLECTED_POSTINGS),
        )

    def listings(self, records: RecordSet, config) -> RecordSet:
        """Search pages: identity, URL and listing facts, keyed by identity."""
        titles_pattern = self.rules["gather_data_selector"]
        website = self.rules["website"]
        usecase = self.rules["usecase"]
        wait_time = self.rules["request_wait_time"]
        more_pages_url_extension = self.rules["more_pages_url_extension"]
        jobs_base_url = self.rules["jobs_base_url"]
        base_url = self.rules["scraping_base_url"]
        postings = {key: deepcopy(record) for key, record in (records or {}).items()}

        def _titleword_from_url(url):
            if url.startswith(base_url):
                return url.removeprefix(base_url).split("&")[0]
            return None

        def _add_listing(soup, titleword):
            for posting_id, posting in parse_listing_soups(
                    [soup], titles_pattern, website, jobs_base_url).items():
                if posting_id in postings:
                    add_matched_titleword(postings[posting_id], titleword)
                    continue
                posting["matched_titlewords"] = [titleword] if titleword else []
                posting["collected_on"] = self.business_day
                postings[posting_id] = posting

        for url in page_urls(self.keywords["titlewords"], base_url):
            titleword = _titleword_from_url(url)
            result = http.requests_responses([url], https=(usecase=="https"),
                                              return_kind="soups", wait_time=wait_time)
            if not result:
                raise RuntimeError(f"Acquisition failed for {url}")
            _add_listing(result[0], titleword)
            row = 25
            get_next_page = has_next_page(result[0], titles_pattern)
            while get_next_page:
                next_page = url + more_pages_url_extension + str(row)
                result = http.requests_responses([next_page], https=(usecase=="https"),
                                                  return_kind="soups", wait_time=wait_time)
                if not result:
                    raise RuntimeError(f"Acquisition failed for {next_page}")
                _add_listing(result[0], titleword)
                get_next_page = has_next_page(result[0], titles_pattern)
                row += 25
        return postings

    def details(self, records: RecordSet, config) -> RecordSet:
        """Fetch one detail page per cache miss and merge the cache hits back in."""
        usecase = self.rules["usecase"]
        wait_time = self.rules["request_wait_time"]
        cached_hits, postings = split_cached_postings(
            {key: deepcopy(record) for key, record in (records or {}).items()},
            cached_postings=getattr(config, "cached_postings", None),
            cache_mode=getattr(config, "cache_mode", None),
            cache_hit_predicate=getattr(config, "cache_hit_predicate", None),
        )
        for posting_id, posting in postings.items():
            # One request per posting so a failed detail cannot shift another ID's soup.
            result = http.requests_responses([posting["url"]], https=(usecase=="https"),
                                              return_kind="soups", wait_time=wait_time)
            if result:
                posting.update(
                    parse_detail_soups({posting_id: result[0]}).get(posting_id, {})
                )
        return {**cached_hits, **postings}

    def gather_data(
        self,
        url_links=None,
        descriptions=False,
        verbose=False,
        transformations=None,
        description_key="description",
        cached_postings=None,
        cache_mode=None,
        cache_hit_predicate=None,
        process=True,
    ):
        if not process:
            config = SimpleNamespace(
                cached_postings=cached_postings,
                cache_mode=cache_mode,
                cache_hit_predicate=cache_hit_predicate,
            )
            postings = self.listings({}, config)
            if descriptions:
                postings = self.details(postings, config)
            return factual_postings(postings)

        titles_pattern = self.rules["gather_data_selector"]
        website = self.rules["website"]
        usecase = self.rules["usecase"]
        request_wait_time = self.rules.get("request_wait_time", 0.16)
        more_pages_url_extension = self.rules["more_pages_url_extension"]
        jobs_base_url = self.rules["jobs_base_url"]

        if transformations is None:
            transformations = []
        if not url_links:
            url_links = page_urls(self.keywords["titlewords"], self.rules["scraping_base_url"])

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
                        "collected_on": self.business_day,
                    }
                else:
                    _add_matched_titleword(postings[posting_id], matched_titleword)

        def _next_page(soup):
            return has_next_page(soup, titles_pattern)

        for url in url_links:
            matched_titleword = _titleword_from_url(url)
            result = http.requests_responses([url], https=(usecase=="https"),
                                              return_kind="soups", wait_time=request_wait_time,
                                              verbose=verbose)
            if not result:
                if verbose:
                    print(f"No response received for {url}, skipping...")
                continue
            soup = result[0]
            _add_postings_from_soup(soup, matched_titleword)
            row = 25
            get_next_page = _next_page(soup)
            while get_next_page:
                if verbose:
                    print(f"Getting next page for {url}")
                next_page = url + more_pages_url_extension + str(row)
                result = http.requests_responses([next_page], https=(usecase=="https"),
                                                  return_kind="soups", wait_time=request_wait_time,
                                                  verbose=verbose)
                if not result:
                    if verbose:
                        print(f"No response for next page {next_page}, stopping pagination...")
                    break
                soup = result[0]
                _add_postings_from_soup(soup, matched_titleword)
                get_next_page = _next_page(soup)
                row += 25

        postings = self._filter_postings(postings)
        cached_hits, postings = split_cached_postings(
            postings,
            cached_postings=cached_postings,
            cache_mode=cache_mode,
            cache_hit_predicate=cache_hit_predicate,
        )

        if descriptions:
            url_list = [posting["url"] for posting in postings.values()]
            ids = [website+re.search(r'/\d+/$', url).group().replace("/", "") for url in url_list]
            soups = http.requests_responses(url_list, https=(usecase=="https"),
                                              return_kind="soups", wait_time=request_wait_time,
                                              verbose=verbose)
            #Match ids to soups (if some requests failed, soups may be shorter)
            ids_soups = dict(zip(ids[:len(soups)], soups))
            descriptions = parse_detail_soups(ids_soups, verbose=verbose)
            for _id, posting in descriptions.items():
                postings[_id] = {'id':_id, 'title':postings[_id]["title"],
                                'company':postings[_id]["company"],
                                **posting, 'url':postings[_id]["url"],
                                'source':postings[_id]["source"],
                                "collected_on": self.business_day,
                                }

        postings = self._process_data(postings, transformations=transformations, description_key=description_key)
        postings = {**cached_hits, **postings}
        return postings

