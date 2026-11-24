"""HTTP request helpers: one session, timeout, retry and backoff."""

import time

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, Timeout

from jobscraping.config.constants import (
    BACKOFF_DURATION,
    CONSECUTIVE_FAILURES_THRESHOLD,
    DEFAULT_REQUEST_TIMEOUT,
    RETRY_TIMEOUT,
)


def requests_responses(
    urls,
    return_kind="responses",
    https=False,
    headers=None,
    wait_time=0.3,
    timeout=None,
    verbose=False,
):  # pylint: disable=too-many-arguments,too-many-locals,too-many-branches
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
    retry_later = []  # (url, index) tuples
    consecutive_failures = 0
    if headers is None:
        headers = {}
    else:
        headers = dict(headers)

    session = requests.Session()
    if https:
        if "User-Agent" not in headers:
            headers["User-Agent"] = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/58.0.3029.110 Safari/537.3"
            )

    for idx, url in enumerate(urls):
        if wait_time:
            time.sleep(wait_time)
        try:
            response = session.get(url, headers=headers, timeout=timeout)
            responses.append(response)
            consecutive_failures = 0

        except (Timeout, RequestException) as error:
            if verbose:
                print(f"Request failed for {url}: {type(error).__name__} - {error}")
            retry_later.append((url, idx))
            responses.append(None)  # placeholder
            consecutive_failures += 1

            if consecutive_failures >= CONSECUTIVE_FAILURES_THRESHOLD:
                # timeout for repetitive failures
                print(
                    "WARNING: "
                    f"{consecutive_failures} consecutive request failures. "
                    f"Backing off for {BACKOFF_DURATION // 60} minutes..."
                )
                time.sleep(BACKOFF_DURATION)
                consecutive_failures = 0

    # Retry failed requests
    if retry_later:
        if verbose:
            print(
                f"Retrying {len(retry_later)} failed requests with extended timeout..."
            )
        for url, idx in retry_later:
            if wait_time:
                time.sleep(wait_time)
            try:
                response = session.get(url, headers=headers, timeout=RETRY_TIMEOUT)
                responses[idx] = response
                if verbose:
                    print(f"Retry successful for {url}")
            except (Timeout, RequestException) as error:
                if verbose:
                    print(f"Retry failed for {url}: {type(error).__name__} - {error}")
                # Keep None placeholder

    responses = [r for r in responses if r is not None]

    if return_kind == "responses":
        return responses
    if return_kind == "soups":
        soups = [
            BeautifulSoup(response.content, "html.parser") for response in responses
        ]
        return soups

    raise ValueError(f"Unknown return_kind: {return_kind}")


def requests_responses_with_cookies(
    base_url,
    pages,
    base_path,
    referer=None,
    return_kind="responses",
    wait_time=0.3,
    headers=None,
    headers_more=None,
    timeout=None,
    verbose=False,
    stop_condition=None,
    continue_on_http_error=False,
    retry_http_statuses=(429, 500, 502, 503, 504),
    terminal_http_statuses=(),
    raise_on_retry_failure=False,
    raise_on_http_error=False,
):  # pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
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
        stop_condition: Optional callable that stops pagination after a successful response
        continue_on_http_error: Continue with later pages after a non-retryable error
        retry_http_statuses: HTTP statuses to retry once with an extended timeout
        terminal_http_statuses: HTTP statuses that end pagination after a successful page
        raise_on_retry_failure: Raise instead of returning partial data after a failed retry

    Returns:
        List of responses or BeautifulSoup objects
    """
    if timeout is None:
        timeout = DEFAULT_REQUEST_TIMEOUT

    if headers is None:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "Path": base_path + "&page=1",
        }
        if referer:
            headers["Referer"] = referer
    else:
        headers = dict(headers)
    if headers_more:
        headers.update(headers_more)

    responses = []
    retry_later = []  # (page, index) tuples for failed requests
    consecutive_failures = 0

    session = requests.Session()
    for page in pages:
        url = base_url + str(page)
        path = base_path + str(page)
        headers["Path"] = path
        if wait_time:
            time.sleep(wait_time)

        try:
            response = session.get(url, headers=headers, timeout=timeout)
            if response.status_code != 200:
                if response.status_code in terminal_http_statuses and responses:
                    if verbose:
                        print(f"Stopped at page {page}, error: {response.status_code}")
                    break
                if response.status_code in retry_http_statuses:
                    retry_later.append((page, len(responses)))
                    if verbose:
                        print(
                            f"Will retry page {page}, error: {response.status_code}"
                        )
                    if continue_on_http_error:
                        continue
                    break
                if verbose:
                    print(f"Stopped at page {page}, error: {response.status_code}")
                if raise_on_http_error:
                    raise RuntimeError(f"Acquisition failed for {url}: HTTP {response.status_code}")
                if continue_on_http_error:
                    continue
                break
            responses.append(response)
            consecutive_failures = 0  # Reset on success
            for cookie in response.cookies:
                session.cookies.set(cookie.name, cookie.value)
            if stop_condition is not None and stop_condition(response):
                break

        except (Timeout, RequestException) as error:
            if verbose:
                print(
                    f"Request failed for page {page} ({url}): "
                    f"{type(error).__name__} - {error}"
                )
            retry_later.append((page, len(responses)))
            consecutive_failures += 1

            if consecutive_failures >= CONSECUTIVE_FAILURES_THRESHOLD:
                print(
                    "WARNING: "
                    f"{consecutive_failures} consecutive request failures. "
                    f"Backing off for {BACKOFF_DURATION // 60} minutes..."
                )
                time.sleep(BACKOFF_DURATION)
                consecutive_failures = 0

    # Retry failed requests (insert at correct positions)
    if retry_later:
        if verbose:
            print(
                f"Retrying {len(retry_later)} failed requests with extended timeout..."
            )
        retry_responses = []
        retry_failures = []
        for page, original_idx in retry_later:
            url = base_url + str(page)
            path = base_path + str(page)
            headers["Path"] = path
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
                    retry_failures.append((page, response.status_code))
                    if verbose:
                        print(
                            f"Retry got status {response.status_code} for page {page}"
                        )
            except (Timeout, RequestException) as error:
                retry_failures.append((page, type(error).__name__))
                if verbose:
                    print(
                        f"Retry failed for page {page}: {type(error).__name__} - {error}"
                    )

        # Insert retry responses at correct positions
        for original_idx, response in sorted(
            retry_responses, key=lambda x: x[0], reverse=True
        ):
            responses.insert(original_idx, response)

        if retry_failures and raise_on_retry_failure:
            failures = ", ".join(
                f"{page} ({reason})" for page, reason in retry_failures
            )
            raise RuntimeError(f"HTTP retries failed for: {failures}")

    if return_kind == "responses":
        return responses
    if return_kind == "soups":
        soups = [
            BeautifulSoup(response.content, "html.parser") for response in responses
        ]
        return soups

    raise ValueError(f"Unknown return_kind: {return_kind}")


def process_site_urls(urls, usecase="http", **kwargs):
    """Note: Can also return responses instead of soups."""
    # TRANSITIONAL: this dispatch mixes the HTTP and browser paths. HTTP scraping
    # (and therefore http.py) must not contain Selenium; a headless-browser fetch
    # path is expected to replace this. Kept only until that path exists.
    if usecase == "http":
        soups = requests_responses(urls, **kwargs)
        return soups

    if usecase == "https":
        soups = requests_responses(urls, https=True, **kwargs)
        return soups

    if usecase == "http_cookies":
        soups = requests_responses_with_cookies(urls, **kwargs)
        return soups

    if usecase == "selenium":
        from jobscraping.scrapers import browser      # local: keeps http Selenium-free
        soups = browser.scroll_scrape_websites(urls, **kwargs)
        return soups

    if usecase == "http_selenium":
        # Planned use: first try HTTP(S); on a condition, retry via Selenium.
        raise ValueError(f"Unknown method: {usecase}")

    if usecase == "click":
        raise ValueError(f"Unknown method: {usecase}")

    raise ValueError(f"Unknown method: {usecase}")
