"""Headless-browser helpers: Selenium session, popups and scrolling."""

from __future__ import annotations

import time
from typing import Callable

from bs4 import BeautifulSoup


try:
    from selenium import webdriver  # pylint: disable=import-error
    from selenium.common.exceptions import (  # pylint: disable=import-error
        ElementClickInterceptedException,
        ElementNotInteractableException,
        NoSuchElementException,
        TimeoutException,
    )
    from selenium.webdriver.support import (
        expected_conditions,  # pylint: disable=import-error
    )
    from selenium.webdriver.support.ui import (
        WebDriverWait,  # pylint: disable=import-error
    )
except ModuleNotFoundError:
    # pylint: disable=invalid-name
    webdriver = None
    WebDriverWait = None
    expected_conditions = None
    NoSuchElementException = None
    ElementClickInterceptedException = None
    ElementNotInteractableException = None
    TimeoutException = None
    # pylint: enable=invalid-name


GET_HEIGHT_SCRIPT = "return document.body.scrollHeight"
SCROLL_DOWN_SCRIPT = "window.scrollTo(0, document.body.scrollHeight);"
SCROLL_1000_SCRIPT = "window.scrollTo(0, 1000);"
CSS_SELECTOR = "css selector"


def _require_selenium():
    if webdriver is None:
        raise ModuleNotFoundError("Selenium package is required for this operation")


def press_button_until_gone(
    button_selector,
    url=None,
    first_wait=1.0,
    pre_click_wait=0.0,
    post_click_wait=0.0,
    scroll=True,
    driver: webdriver.Firefox = None,
    close_driver=True,
    open_page=True,
):  # pylint: disable=too-many-arguments
    """
    Continuously presses a button on a webpage until it no longer exists.
    """
    _require_selenium()
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

            except (
                NoSuchElementException,
                ElementClickInterceptedException,
                ElementNotInteractableException,
            ):
                break

        soup = BeautifulSoup(driver.page_source, "html.parser")

    finally:
        if close_driver:
            driver.quit()

    return soup


def close_popup(
    button_selector,
    url=None,
    driver: webdriver.Firefox = None,
    click_wait=12.0,
    pre_click_scroll=False,
    post_click_wait=0.0,
    post_click_scroll=False,
    close_driver=True,
    open_page=True,
):  # pylint: disable=too-many-arguments
    """Close cookie popups."""
    _require_selenium()
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
        except (
            NoSuchElementException,
            ElementClickInterceptedException,
            ElementNotInteractableException,
        ):
            pass
        if post_click_wait:
            time.sleep(post_click_wait)
        soup = BeautifulSoup(driver.page_source, "html.parser")
    except TimeoutException:
        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        if close_driver:
            driver.quit()
    return soup


def scroll_scrape_websites(
    urls,
    driver: webdriver.Firefox = None,
    close_driver=True,
    wait_time=2.0,
    pre_scrolling_wait=2.0,
):
    """Scroll down each URL until content stops changing."""
    _require_selenium()
    if driver is None:
        driver = webdriver.Firefox()

    all_soups = []
    for url in urls:
        driver.get(url)
        last_height = driver.execute_script(GET_HEIGHT_SCRIPT)
        step_counter = 0

        time.sleep(pre_scrolling_wait)
        while step_counter < 100:
            step_counter += 1
            driver.execute_script(SCROLL_DOWN_SCRIPT)
            time.sleep(wait_time)
            new_height = driver.execute_script(GET_HEIGHT_SCRIPT)
            if new_height == last_height:
                if step_counter == 1:
                    continue
                break
            last_height = new_height

        soup = BeautifulSoup(driver.page_source, "html.parser")
        all_soups.append(soup)
    if close_driver:
        driver.quit()
    return all_soups


def scroll_scrape_website(
    url=None,
    driver: webdriver.Firefox = None,
    close_driver=True,
    wait_time=2.0,
    pre_first_scroll_wait=2.0,
    open_page=True,
):  # pylint: disable=too-many-arguments
    """Scroll down a single URL until content stops changing."""
    _require_selenium()
    if driver is None:
        driver = webdriver.Firefox()
    if url and open_page:
        driver.get(url)

    last_height = driver.execute_script(GET_HEIGHT_SCRIPT)
    step_counter = 0

    time.sleep(pre_first_scroll_wait)
    while step_counter < 100:
        step_counter += 1
        driver.execute_script(SCROLL_DOWN_SCRIPT)
        time.sleep(wait_time)
        new_height = driver.execute_script(GET_HEIGHT_SCRIPT)
        if new_height == last_height:
            if step_counter == 1:
                continue
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, "html.parser")
    if close_driver:
        driver.quit()
    return soup


def close_website_popup(
    driver: webdriver.Firefox,
    button_selector,
    url=None,
    click_wait=12.0,
    pre_click_scroll=False,
    post_click_wait=0.0,
    post_click_scroll_down=False,
    close_driver=True,
    open_page=True,
):  # pylint: disable=too-many-arguments
    """Close cookie popups."""
    _require_selenium()
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
        except (
            NoSuchElementException,
            ElementClickInterceptedException,
            ElementNotInteractableException,
        ):
            pass
        if post_click_wait:
            time.sleep(post_click_wait)
        soup = BeautifulSoup(driver.page_source, "html.parser")
    except TimeoutException:
        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        if close_driver:
            driver.quit()
    return soup


def load_page(
    url,
    driver: webdriver.Firefox = None,
    close_popup=True,
    close_popup_method: Callable = close_website_popup,
    load_more_button=True,
    load_by_scrolling=False,
    popup_wait=12.0,
    pre_popup_scroll=True,
    popup_selector=None,
    post_popup_close_wait=0.3,
    post_popup_close_scroll_down=True,
    action_wait=1.1,
    first_action_wait=2.0,
    post_load_more_wait=0.1,
    load_more_selector=None,
    close_driver=False,
):  # pylint: disable=too-many-arguments,too-many-locals,redefined-outer-name
    """
    General function for loading pages and handling popups, buttons, and scrolling.

    Parameters:
    url: str
        The url of the website to load.
    close_popup: bool
        If True, close the popup window.
    close_popup_method: Callable
        The method to use for closing the popup. By default, uses
        close_website_popup but can be replaced in site scraper classes.
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
        Time to wait after pressing "Load more" or scrolling down.
    first_action_wait: float
        Time to wait before the first action.
    post_load_more_wait: float
        Time to wait after pressing the "Load more" button.
    close_driver: bool
        If True, close the driver after finishing the process.

    Returns:
    final_page_soup: BeautifulSoup
        The final page soup after all actions have been performed.
    """
    _require_selenium()
    if driver is None:
        driver = webdriver.Firefox()

    driver.get(url)

    if close_popup and popup_selector:
        close_popup_method(
            driver,
            popup_selector,
            url=None,
            click_wait=popup_wait,
            pre_click_scroll=pre_popup_scroll,
            post_click_wait=post_popup_close_wait,
            post_click_scroll_down=post_popup_close_scroll_down,
            close_driver=False,
            open_page=False,
        )

    if load_more_button and load_more_selector:
        final_page_soup = press_button_until_gone(
            load_more_selector,
            url=None,
            first_wait=first_action_wait,
            pre_click_wait=action_wait,
            post_click_wait=post_load_more_wait,
            scroll=True,
            open_page=False,
            driver=driver,
            close_driver=False,
        )
    elif load_by_scrolling:
        final_page_soup = scroll_scrape_website(
            url=None,
            driver=driver,
            close_driver=False,
            wait_time=action_wait,
            pre_first_scroll_wait=first_action_wait,
            open_page=False,
        )
    else:
        final_page_soup = BeautifulSoup(driver.page_source, "html.parser")

    if close_driver:
        driver.quit()
    return final_page_soup


def load_pages(
    urls,
    close_popup="first",
    popup_closing_wait=12.0,
    driver: webdriver.Firefox = None,
    page_load_method: Callable = load_page,
    load_more_button=True,
    load_by_scrolling=False,
    post_click_wait=0.0,
    close_driver=True,
    **kwargs,
):  # pylint: disable=too-many-arguments,redefined-outer-name
    """Load multiple pages and return their soups."""
    _require_selenium()
    if driver is None:
        driver = webdriver.Firefox()
    all_soups = []

    if close_popup in ["none", False]:
        close_popup_enabled = False
    else:
        close_popup_enabled = True

    for index, url in enumerate(urls):
        soup = page_load_method(
            url,
            close_popup=close_popup_enabled,
            popup_wait=popup_closing_wait,
            load_more_button=load_more_button,
            load_by_scrolling=load_by_scrolling,
            post_click_wait=post_click_wait,
            close_driver=False,
            **kwargs,
        )
        if index == 0 and close_popup == "first":
            close_popup_enabled = False
        all_soups.append(soup)

    if close_driver:
        driver.quit()
    return all_soups
