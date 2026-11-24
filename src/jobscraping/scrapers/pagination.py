"""Pagination helpers shared by the HTTP and headless-browser paths."""

from __future__ import annotations

from bs4 import BeautifulSoup


def next_page_logic_by_length(data: BeautifulSoup, pattern: str, lengths: list):
    """Input is typically a soup or HTML element, possibly dict or string."""
    if not isinstance(data, BeautifulSoup):
        data = BeautifulSoup(data, "html.parser")
    selects = data.select(pattern)
    if len(selects) in lengths:
        return True
    return False
