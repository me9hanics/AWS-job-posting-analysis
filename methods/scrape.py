import requests
from requests.exceptions import Timeout, RequestException
from bs4 import BeautifulSoup
from typing import Callable, List, Tuple
import time

try:
    from methods.constants import (
        DEFAULT_REQUEST_TIMEOUT, RETRY_TIMEOUT,
        BACKOFF_DURATION, CONSECUTIVE_FAILURES_THRESHOLD
    )
except ModuleNotFoundError:
    from constants import (
        DEFAULT_REQUEST_TIMEOUT, RETRY_TIMEOUT,
        BACKOFF_DURATION, CONSECUTIVE_FAILURES_THRESHOLD
    )

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
                            scroll=True, driver: webdriver.Firefox = None,
                            close_driver=True, open_page = True):
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


def close_popup(button_selector, url=None, driver: webdriver.Firefox = None,
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


def scroll_scrape_websites(urls, driver: webdriver.Firefox = None, close_driver = True,
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


def scroll_scrape_website(url=None, driver: webdriver.Firefox = None, close_driver = True,
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


def requests_responses(urls, return_kind = 'responses', https = False,
                       headers = {}, wait_time = 0.3, timeout = None,
                       verbose = False):
    """
    Make HTTP requests to a list of URLs with timeout, retry, and backoff logic.
    
    Args:
        urls: List of URLs to request
        return_kind: 'responses' or 'soups'
        https: Whether to use HTTPS headers
        headers: Custom headers dict
        wait_time: Time to wait between requests
        timeout: Request timeout in seconds (default: DEFAULT_REQUEST_TIMEOUT)
        verbose: Print status messages
    
    Returns:
        List of responses or BeautifulSoup objects
    """
    if timeout is None:
        timeout = DEFAULT_REQUEST_TIMEOUT
    
    responses = []
    retry_later = []  #(url, index) tuples
    consecutive_failures = 0
    
    session = requests.Session()
    if https:
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    
    for idx, url in enumerate(urls):
        if wait_time:
            time.sleep(wait_time)        
        try:
            response = session.get(url, headers=headers, timeout=timeout)
            responses.append(response)
            consecutive_failures = 0 
            
        except (Timeout, RequestException) as e:
            if verbose:
                print(f"Request failed for {url}: {type(e).__name__} - {e}")
            retry_later.append((url, idx))
            responses.append(None) #placeholder
            consecutive_failures += 1
            
            if consecutive_failures >= CONSECUTIVE_FAILURES_THRESHOLD:
                #timeout for repetitive failures
                print(f"WARNING: {consecutive_failures} consecutive request failures. Backing off for {BACKOFF_DURATION // 60} minutes...")
                time.sleep(BACKOFF_DURATION)
                consecutive_failures = 0
    
    #Retry failed requests
    if retry_later:
        if verbose:
            print(f"Retrying {len(retry_later)} failed requests with extended timeout...")
        for url, idx in retry_later:
            if wait_time:
                time.sleep(wait_time)
            try:
                response = session.get(url, headers=headers, timeout=RETRY_TIMEOUT)
                responses[idx] = response
                if verbose:
                    print(f"Retry successful for {url}")
            except (Timeout, RequestException) as e:
                if verbose:
                    print(f"Retry failed for {url}: {type(e).__name__} - {e}")
                # Keep None placeholder
    
    responses = [r for r in responses if r is not None]
    
    if return_kind == 'responses':
        return responses
    if return_kind == 'soups':
        soups = [BeautifulSoup(response.content, 'html.parser') for response in responses]
        return soups
    
    raise ValueError(f'Unknown return_kind: {return_kind}')


def requests_responses_with_cookies(base_url, pages, base_path, referer=None,
                                    return_kind = 'responses', wait_time = 0.3,
                                    headers = {}, headers_more = {},
                                    timeout = None, verbose = False):
    """
    Make HTTP requests with cookie persistence, timeout, retry, and backoff logic.
    
    Args:
        base_url: Base URL to append pages to
        pages: List of page identifiers to append to base_url
        base_path: Base path for headers
        referer: Referer header value
        return_kind: 'responses' or 'soups'
        wait_time: Time to wait between requests
        headers: Custom headers dict
        headers_more: Additional headers to merge
        timeout: Request timeout in seconds (default: DEFAULT_REQUEST_TIMEOUT)
        verbose: Print status messages
    
    Returns:
        List of responses or BeautifulSoup objects
    """
    if timeout is None:
        timeout = DEFAULT_REQUEST_TIMEOUT
    
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
    retry_later = []  #(page, index) tuples for failed requests
    consecutive_failures = 0
    
    session = requests.Session()
    for idx, page in enumerate(pages):
        url = base_url + str(page)
        path = base_path + str(page)
        headers['Path'] = path
        if wait_time:
            time.sleep(wait_time)
        
        try:
            response = session.get(url, headers=headers, timeout=timeout)
            if response.status_code != 200:
                if verbose:
                    print(f"Stopped at page {page}, error: {response.status_code}")
                break
            responses.append(response)
            consecutive_failures = 0  # Reset on success
            for cookie in response.cookies:
                session.cookies.set(cookie.name, cookie.value)
                
        except (Timeout, RequestException) as e:
            if verbose:
                print(f"Request failed for page {page} ({url}): {type(e).__name__} - {e}")
            retry_later.append((page, len(responses)))  # Track position for retry
            consecutive_failures += 1
            
            if consecutive_failures >= CONSECUTIVE_FAILURES_THRESHOLD:
                print(f"WARNING: {consecutive_failures} consecutive request failures. Backing off for {BACKOFF_DURATION // 60} minutes...")
                time.sleep(BACKOFF_DURATION)
                consecutive_failures = 0  # Reset after backoff
    
    # Retry failed requests (insert at correct positions)
    if retry_later:
        if verbose:
            print(f"Retrying {len(retry_later)} failed requests with extended timeout...")
        retry_responses = []
        for page, original_idx in retry_later:
            url = base_url + str(page)
            path = base_path + str(page)
            headers['Path'] = path
            if wait_time:
                time.sleep(wait_time)
            try:
                response = session.get(url, headers=headers, timeout=RETRY_TIMEOUT)
                if response.status_code == 200:
                    retry_responses.append((original_idx, response))
                    if verbose:
                        print(f"Retry successful for page {page}")
                    for cookie in response.cookies:
                        session.cookies.set(cookie.name, cookie.value)
                else:
                    if verbose:
                        print(f"Retry got status {response.status_code} for page {page}")
            except (Timeout, RequestException) as e:
                if verbose:
                    print(f"Retry failed for page {page}: {type(e).__name__} - {e}")
        
        # Insert retry responses at correct positions
        for original_idx, response in sorted(retry_responses, key=lambda x: x[0], reverse=True):
            responses.insert(original_idx, response)
    
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

def close_website_popup(driver: webdriver.Firefox, button_selector, url=None, 
                        click_wait=12.0, pre_click_scroll=False, 
                        post_click_wait = 0.0, post_click_scroll_down=False, 
                        close_driver=True, open_page=True):
    """
    Close cookie popups
    """
    #if driver is None:
    #    driver = webdriver.Firefox()
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

def load_page(url, driver: webdriver.Firefox =None, close_popup=True,
              close_popup_method: Callable = close_website_popup,
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
    if driver is None:
        driver = webdriver.Firefox()
    
    driver.get(url)
    
    if close_popup and popup_selector:
        close_popup_method(driver, popup_selector, url=None, click_wait=popup_wait,
                           pre_click_scroll=pre_popup_scroll,
                           post_click_wait=post_popup_close_wait,
                           post_click_scroll_down=post_popup_close_scroll_down,
                           close_driver=False, open_page=False)

    if load_more_button and load_more_selector:
        final_page_soup = press_button_until_gone(load_more_selector, url = None,
                                                  first_wait=first_action_wait,
                                                  pre_click_wait=action_wait,
                                                  post_click_wait=post_load_more_wait,
                                                  scroll=True, open_page=False,
                                                  driver=driver, close_driver=False)
    elif load_by_scrolling:
        final_page_soup = scroll_scrape_website(url=None, driver=driver, close_driver=False,
                                                wait_time=action_wait, pre_first_scroll_wait=first_action_wait,
                                                open_page=False)
    else:
        final_page_soup = BeautifulSoup(driver.page_source, 'html.parser')

    if close_driver:
        driver.quit()
    return final_page_soup

def load_pages(urls, close_popup="first", popup_closing_wait=12.0,
               driver: webdriver.Firefox = None,
               page_load_method: Callable = load_page,
               load_more_button = True, load_by_scrolling = False,
               post_click_wait = 0.0, close_driver=True, **kwargs):
        if driver is None:
            driver = webdriver.Firefox()
        all_soups = []

        if close_popup in ["none", False]:
            _close_popup_bool = False
        else:
            _close_popup_bool = True

        for i,url in enumerate(urls):
            soup = page_load_method(url, close_popup =_close_popup_bool, popup_wait=popup_closing_wait,
                                  load_more_button = load_more_button, load_by_scrolling=load_by_scrolling,
                                  post_click_wait = post_click_wait, close_driver=False, **kwargs)
            if i==0 and close_popup == "first":
                _close_popup_bool = False
            all_soups.append(soup)

        if close_driver:
            driver.quit()
        return all_soups

def next_page_logic_by_length(input:BeautifulSoup, pattern: str, lengths: list):
    """input: typically a soup or HTML element, possibly dict or string"""
    if not isinstance(input, BeautifulSoup):
        input = BeautifulSoup(input, 'html.parser')
    selects = input.select(pattern)
    if len(selects) in lengths:
        return True
    return False