import requests
from bs4 import BeautifulSoup
import time

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, TimeoutException

GET_HEIGHT_SCRIPT = "return document.body.scrollHeight"
SCROLL_DOWN_SCRIPT = "window.scrollTo(0, document.body.scrollHeight);" #scroll to height value of the bottom of the page
SCROLL_1000_SCRIPT = "window.scrollTo(0, 1000);"
CSS_SELECTOR = "css selector" #can use instead: from selenium.webdriver.common.by import By, then By.CSS_SELECTOR

def press_button_until_gone(button_selector, url=None, first_wait=1.0, 
                            pre_click_wait=0.0, post_click_wait=0.0,
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
        time.sleep(first_wait)
        while step_counter < 100:
            try:
                if scroll:
                    driver.execute_script(SCROLL_DOWN_SCRIPT)
                time.sleep(pre_click_wait)
                button = driver.find_element(CSS_SELECTOR, button_selector)
                button.click()
                time.sleep(post_click_wait)
                step_counter += 1
            
            except (NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException):
                break

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
    finally:
        if close_driver:
            driver.quit()
    
    return soup


def close_popup(button_selector, url=None, 
                        click_wait=12.0, pre_click_scroll=False, 
                        post_click_wait = 0.0, post_click_scroll=False, 
                        close_driver=True, open_page=True):
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
            if pre_click_scroll:
                driver.execute_script(SCROLL_DOWN_SCRIPT)
            button = driver.find_element(CSS_SELECTOR, button_selector)
            button.click()
            if post_click_scroll:
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


def scroll_scrape_websites(urls, driver = None, close_driver = True,
                           wait_time = 2.0, pre_scrolling_wait = 2.0):
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


def scroll_scrape_website(url=None, driver = None, close_driver = True,
                          wait_time = 2.0, pre_first_scroll_wait = 2.0, open_page=True):
    if driver is None:
        driver = webdriver.Firefox()
    if url and open_page:
        driver.get(url)
        
    last_height = driver.execute_script(GET_HEIGHT_SCRIPT)
    step_counter = 0

    time.sleep(pre_first_scroll_wait)
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


def requests_responses(urls, return_kind = 'soups', https = False,
                       headers = {}, wait_time = 0.3):
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


def requests_responses_with_cookies(base_url, pages, base_path, referer=None,
                                    return_kind = 'responses', wait_time = 0.3,
                                    headers = {}, headers_more = {},
                                    verbose = False):
    if not headers:
        headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'Path': base_path + "&page=1",
            }
        if referer:
            headers['Referer'] = referer
    headers.update(headers_more)

    responses = []
    session = requests.Session()
    for page in pages:
        url = base_url + str(page)
        path = base_path + str(page)
        headers['Path'] = path
        if wait_time:
            time.sleep(wait_time)
        response = session.get(url, headers = headers)
        if response.status_code != 200:
            if verbose:
                print(f"Stopped at page {page}, error: {response.status_code}")
            break
        responses.append(response)
        for cookie in response.cookies:
            session.cookies.set(cookie.name, cookie.value)
        
    if return_kind == 'responses':
        return responses
    if return_kind == 'soups':
        soups = [BeautifulSoup(response.content, 'html.parser') for response in responses]
        return soups
    
    raise ValueError(f'Unknown return_kind: {return_kind}')


def process_site_urls(urls, usecase='http', **kwargs):
    """
    Note: Can also return responses instead of soups
    """
    if usecase == 'http':
        soups = requests_responses(urls, **kwargs)
        return soups
    
    if usecase == 'https':
        soups = requests_responses(urls, https = True, **kwargs)
        return soups
    
    if usecase == 'http_cookies':
        soups = requests_responses_with_cookies(urls, **kwargs)
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