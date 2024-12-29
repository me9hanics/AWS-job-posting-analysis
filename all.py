import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import re
import json
import requests
import itertools

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, TimeoutException

GET_HEIGHT_SCRIPT = "return document.body.scrollHeight"
SCROLL_DOWN_SCRIPT = "window.scrollTo(0, document.body.scrollHeight);" #scroll to height value of the bottom of the page
SCROLL_1000_SCRIPT = "window.scrollTo(0, 1000);"
CSS_SELECTOR = "css selector" #can use instead: from selenium.webdriver.common.by import By, then By.CSS_SELECTOR

def url_builder(base_url, slash_list=[]):
    """Expected strings in slash list (potentially will be extended to dicts)"""
    url = base_url
    if url[-1] == '/':
        url = url[:-1]
    for slash in slash_list:
        url += '/' + slash
    return url

def urls_builder(base_url, slash_elements_list = [], zipped = True, all_combinations = False):
    """expecting list of lists"""
    urls = []
    if zipped:
        if all_combinations:
            slash_lists = list(set(itertools.product(*slash_elements_list)))
        else:
            slash_lists = list(zip(*slash_elements_list))
    else:
        
        slash_lists = slash_elements_list
    for slash_list in slash_lists:
            urls.append(url_builder(base_url, slash_list))
    return urls

def press_button_until_gone(button_selector, url=None, wait_time=2, 
                            pre_click_wait=0, post_click_wait=0,
                            scroll=True, driver = None, close_driver=True, open_page = True):
    """
    Continuously presses a button on a webpage until it no longer exists.
    """
    if driver is None:
        driver = webdriver.Firefox()
    if url and open_page:
        driver.get(url)
    step_counter = 0
    
    try:
        time.sleep(pre_click_wait)
        while step_counter < 100:
            try:
                if scroll:
                    driver.execute_script(SCROLL_DOWN_SCRIPT)
                time.sleep(wait_time/2)
                button = driver.find_element(CSS_SELECTOR, button_selector)
                button.click()
                step_counter += 1
                time.sleep(wait_time/2)
            
            except (NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException):
                break

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
    finally:
        if close_driver:
            driver.quit()
    
    return soup


def close_popup(button_selector, url=None, click_wait=12, post_click_wait = 0,
                  pre_scroll=False, post_scroll=False, 
                  driver = None, close_driver=True, open_page=True):
    """
    Close cookie popups
    """
    if driver is None:
        driver = webdriver.Firefox()
    if url and open_page:
        driver.get(url)
    
    try:
        driver.execute_script(SCROLL_1000_SCRIPT)
        WebDriverWait(driver, click_wait).until(
                expected_conditions.element_to_be_clickable((CSS_SELECTOR, button_selector))
        )
        try:
            if pre_scroll:
                driver.execute_script(SCROLL_DOWN_SCRIPT)
            button = driver.find_element(CSS_SELECTOR, button_selector)
            button.click()
            if post_scroll:
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


def scroll_scrape_websites(urls, driver = None, close_driver = True, wait_time = 2, pre_scrolling_wait = 2):
    if driver is None:
        driver = webdriver.Firefox() #only closed after all websites are scraped

    all_soups = []
    for url in urls:
        driver.get(url)
        last_height = driver.execute_script(GET_HEIGHT_SCRIPT)
        step_counter = 0

        time.sleep(pre_scrolling_wait)
        while step_counter<100:
            step_counter += 1
            driver.execute_script(SCROLL_DOWN_SCRIPT)
            time.sleep(wait_time)
            new_height = driver.execute_script(GET_HEIGHT_SCRIPT)
            if new_height == last_height:
                if step_counter == 1:
                    continue
                else:
                    break
            last_height = new_height

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        all_soups.append(soup)
    if close_driver:
        driver.quit()
    return all_soups


def scroll_scrape_website(url=None, driver = None, close_driver = True, wait_time = 2, pre_scrolling_wait = 2, open_page=True):
    if driver is None:
        driver = webdriver.Firefox()
    if url and open_page:
        driver.get(url)
        
    last_height = driver.execute_script(GET_HEIGHT_SCRIPT)
    step_counter = 0

    time.sleep(pre_scrolling_wait)
    while step_counter<100:
        step_counter += 1
        driver.execute_script(SCROLL_DOWN_SCRIPT)  #Scroll to "height"-> bottom of the page
        time.sleep(wait_time)
        new_height = driver.execute_script(GET_HEIGHT_SCRIPT)
        if new_height == last_height:
            if step_counter == 1: #Retry if this is the first iteration - the website may not have loaded properly
                continue
            else:
                break
        last_height = new_height
        
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    if close_driver:
        driver.quit()
    return soup

def requests_responses(urls, return_kind = 'soups', https = False, headers = {}, wait_time = 0.3):
    responses = []
    session = requests.Session()
    if https:
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    for url in urls:
        if wait_time:
            time.sleep(wait_time)
        response = session.get(url, headers = headers)
        responses.append(response)
        
    if return_kind == 'responses':
        return responses
    if return_kind == 'soups':
        soups = [BeautifulSoup(response.content, 'html.parser') for response in responses]
        return soups
    
    raise ValueError(f'Unknown return_kind: {return_kind}')

def process_site_urls(urls, usecase='http', **kwargs):
    if usecase == 'http':
        soups = requests_responses(urls, **kwargs)
        return soups
    
    if usecase == 'https':
        soups = requests_responses(urls, https = True, **kwargs)
        return soups
    
    if usecase == 'selenium':
        soups = scroll_scrape_websites(urls, **kwargs)
        return soups
    
    if usecase == 'http_selenium':
        """Use: e.g. when we do not always want to use Selenium, we first try HTTP(S) and if there is more to load with JS, we use Selenium"""
        #planned use: first try to scrape with http. If a defined condition function returns true, try with selenium
        pass

    if usecase == "click":
        pass
    
    raise ValueError(f'Unknown method: {usecase}')

def load_job_karriereat(url, driver=None, _close_popup=False, wait_time_popup=2, wait=1, close_driver=True, return_url=False):
    if driver is None:
        driver = webdriver.Firefox()
    driver.get(url)
    button_selector = ".onetrust-close-btn-handler"
    if _close_popup:
        close_popup(button_selector, click_wait=wait_time_popup, post_click_wait=0,
                            driver=driver, close_driver=False, open_page=False)
    time.sleep(wait)
    job_soup = BeautifulSoup(driver.page_source, 'html.parser')
    if close_driver:
        driver.quit()

    if return_url:
        return job_soup, url
    return job_soup

def load_jobs_karriereat(urls, driver=None, _close_popup=False, wait_time_popup=2, wait=1, close_driver=True, return_urls=False):
    if driver is None:
        driver = webdriver.Firefox()
    all_soups = []
    returned_urls = []

    for url in urls:
        if return_urls:
            soup, url = load_job_karriereat(url, driver=driver, close_popup=_close_popup, 
                                   wait_time_popup=wait_time_popup, wait=wait, 
                                   close_driver=False, return_url=True)
            returned_urls.append(url)
        else:
            soup = load_job_karriereat(url, driver=driver, close_popup=_close_popup, 
                                       wait_time_popup=wait_time_popup, wait=wait, 
                                       close_driver=False, return_url=False)
        all_soups.append(soup)

    if close_driver:
        driver.quit()

    if return_urls:
        return all_soups, returned_urls
    return all_soups

def load_page_karriereat(url, driver=None, _close_popup=True, wait_time_popup=12, post_click_wait=1.5, close_driver=True):
    if driver is None:
        driver = webdriver.Firefox()
    driver.get(url)
    button_selector = ".onetrust-close-btn-handler"
    if _close_popup:
        close_popup(button_selector, click_wait=wait_time_popup, post_click_wait=post_click_wait,
                            driver=driver, close_driver=False, open_page=False)
    button_selector = ".m-loadMoreJobsButton__button"
    final_page_soup = press_button_until_gone(button_selector, wait_time=4, pre_click_wait=1,
                                                driver=driver, close_driver=False, open_page=False)
    if close_driver:
        driver.quit()
    return final_page_soup

def load_pages_karriereat(urls, driver=None, close_popup="first", click_wait=4, close_driver=True):
    if driver is None:
        driver = webdriver.Firefox()
    all_soups = []
    close_popup_bool = True
    for i,url in enumerate(urls):
        wait = click_wait
        if close_popup=="first":
            if i==0:
                close_popup_bool = True
                wait = 15
            else:
                close_popup_bool = False
        elif (close_popup=="all") | (close_popup==True):
            close_popup_bool = True
            if i==0:
                wait = 15
        elif (close_popup=="none") | (close_popup==False):
            close_popup_bool = False

        soup = load_page_karriereat(url, driver=driver, close_popup=close_popup_bool, wait_time_popup=wait, close_driver=False)
        all_soups.append(soup)

    if close_driver:
        driver.quit()
    return all_soups

def gather_data_karriereat(driver=None, close_driver=True):
    titlewords =["machine-learning","machine-learning-engineer","machine-learning-scientist",
     "ML-scientist", "ML-engineer", "ML-researcher", "ML-developer", "ML-AI",
     "AI-engineer", "AI-scientist", "AI-researcher", "AI-developer", "AI-ML", 
     "data-science","data-scientist", "data-mining",
     "data-engineer", "data-engineering", "data-engineering-developer",
     "data-analysis", "data-analytics", "data-analyst",
     "business-intelligence", "business-intelligence-analyst", "bi-analyst", "business-analyst",
     ]
    locations =["wien-und-umgebung"]*len(titlewords)    
    urls_links = urls_builder('https://www.karriere.at/jobs', [titlewords, locations], zipped = True, all_combinations = False)
    
    if driver is None:
        driver = webdriver.Firefox()
    soups = load_pages_karriereat(urls_links, driver=driver, close_popup="first", close_driver=False)
    pattern = 'div.m-jobsListItem__container div.m-jobsListItem__dataContainer h2.m-jobsListItem__title a.m-jobsListItem__titleLink'
    
    postings = {}
    for soup in soups:
        selects = soup.select(pattern)
        for select in selects:
            id = re.search(r'\d+', select["href"]).group()
            if id not in postings.keys():
                title = select.text
                if title:
                    title = title.strip()
                postings[id] = {"title": title, "url": select["href"], "source": "karriere.at", "id": id}
    
    url_jobs = [posting["url"] for posting in postings.values()]
    soups,returned_urls = load_jobs_karriereat(url_jobs, driver=driver, close_driver=False, return_urls=True)
    ids = [re.search(r'\d+', url).group() for url in returned_urls]

    for i,soup in enumerate(soups):
        description = soup.find("div", class_="m-jobContent__jobText m-jobContent__jobText--standalone")
        if description:
            description = description.text.strip()
        postings[ids[i]]["description"] = description
    
    if close_driver:
        driver.quit()
    return postings

def __main__():
    postings = gather_data_karriereat()
    date_today = time.strftime("%Y-%m-%d")

    with open(f"source/save/postings_{date_today}.json", "w") as f:
        json.dump(postings, f)



if __name__ == "__main__":
    __main__()