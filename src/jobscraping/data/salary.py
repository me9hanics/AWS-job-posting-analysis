"""Salary detection from free text, benefits and description snippets.

Detection is a fact, not a policy: enrichment and scraping both read these
functions without importing a profile or a scraper.
"""

import re
from collections.abc import Callable, Mapping, Sequence

DEFAULT_SALARY_KEYWORDS = {
    "annual": (
        "jährlich",
        "yearly",
        "per year",
        "annual",
        "jährige",
        "pro jahr",
        "p.a.",
    ),
    "monthly": ("monatlich", "monthly", "per month", "pro monat"),
}
DEFAULT_SALARY_REGEXES = (r"\d{6},\d{2}", r"\d{5},\d{2}", r"\d{6}", r"\d{5}")
DEFAULT_DESCRIPTION_REGEXES = (
    r"(Salary|Gehalt|Compensation|Vergütung):.*",
    r"\b(Gross|Brutto|Net|Netto)\b:.*",
    (
        r"(\d{5}[.,]\d+)"
        r"(?:(?!\d{5}[.,]?\d*).)*?\b(netto|brutto|gross)\b"
    ),
    (
        r"(\d{2}[.,]\d{3}[.,]\d+)"
        r"(?:(?!\d{2}[.,]\d{3}[.,]\d*).)*?\b(netto|brutto|gross)\b"
    ),
    (
        r"(\d{4}[.,]\d+)"
        r"(?:(?!\d{4}[.,]?\d*).)*?\b(netto|brutto|gross)\b"
    ),
    (
        r"(\d{1}[.,]\d{3}[.,]\d+)"
        r"(?:(?!\d{1}[.,]\d{3}[.,]\d*).)*?\b(netto|brutto|gross)\b"
    ),
    (
        r"(\d{5})"
        r"(?:(?!\d{5}).)*?\b(netto|brutto|gross)\b"
    ),
    (
        r"(\d{2}[.,]\d{3})"
        r"(?:(?!\d{2}[.,]\d{3}).)*?\b(netto|brutto|gross)\b"
    ),
    (
        r"(\d{5}[.,]\d+)"
        r"(?:(?!\d{5}[.,]?\d*).)*?\b(net|taxes|tax)\b"
    ),
    (
        r"(\d{4}[.,]\d+)"
        r"(?:(?!\d{4}[.,]?\d*).)*?\b(net|taxes|tax)\b"
    ),
    (
        r"(\d{1}[.,]\d{3})"
        r"(?:(?!\d{1}[.,]\d{3}).)*?\b(netto|brutto|gross)\b"
    ),
    r"\d{4,5}[.,]\d{2}",
    r"(\d{5})(?:(?!\d{5}).)*?\b(net|taxes|tax)\b",
)


def salary_number_from_str(
    text: str,
    keywords: Sequence[str] | None = None,
    remove_chars: Sequence[str] = (".",),
    lengths: Sequence[int] | None = None,
):
    """Extract a salary number from free text using optional keywords."""
    if not isinstance(text, str):
        return None
    if lengths is None:
        lengths = (6, 5)
    if keywords is None:
        keywords = []
    for char in remove_chars:
        text_cleaned = text.replace(char, "")
    if not keywords:
        for length in lengths:
            #Search for length-digit numbers
            value = re.search(rf'\d{{{length}}}', text_cleaned)
            if value:
                return int(value.group())
    else:
        if any(keyword in text for keyword in keywords):
            for length in lengths:
                value = re.search(rf'\d{{{length}}}', text_cleaned)
                if value:
                    return int(value.group())
    return None


def salary_regex(
    text: str,
    regexes: Sequence[str] = DEFAULT_SALARY_REGEXES,
    decimal_separator: str = ",",
):
    """Extract a salary number using a list of regex patterns."""
    for regex in regexes:
        value = re.search(regex, text)
        if value:
            try:
                return int(value.group())
            except ValueError:
                return int(float(value.group().replace(decimal_separator, ".")))
    return None


def salary_from_text(
    text: str,
    keywords: Mapping[str, Sequence[str]] | None = None,
    clarity_comma_char: str = ".",
    decimal_separator: str = ",",
    conversion_rate: int = 12,
    lengths: Sequence[int] | None = None, #(6, 5)
):
    """Parse salary numbers from a text string."""
    if not isinstance(text, str):
        return None
    if keywords is None:
        keywords = DEFAULT_SALARY_KEYWORDS
    text = text.lower()
    salary = {}
    if "annual" in keywords:
        value = salary_number_from_str(
            text,
            keywords["annual"],
            remove_chars=[clarity_comma_char],
            lengths=lengths,
        )
        if value:
            salary["annual"] = value
    if (not salary) and ("monthly" in keywords):
        value = salary_regex(
            text.replace(clarity_comma_char, ""),
            decimal_separator=decimal_separator,
            regexes=[rf"\d{{4}}{decimal_separator}\d{{2}}"],
        )
        if not value:
            value = salary_number_from_str(
                text,
                keywords["monthly"],
                remove_chars=[clarity_comma_char],
                lengths=[4],
            )
        if value:
            salary["monthly"] = value
    if not salary:
        value = salary_regex(
            text.replace(clarity_comma_char, ""),
            decimal_separator=decimal_separator,
            regexes=[
                rf"\d{{6}}{decimal_separator}\d{{2}}",
                rf"\d{{5}}{decimal_separator}\d{{2}}",
                r"\d{6}",
                r"\d{5}",
            ],
        )
        if value:
            salary["annual"] = value
        else:
            value = salary_regex(
                text.replace(clarity_comma_char, ""),
                decimal_separator=decimal_separator,
                regexes=[rf"\d{{4}}{decimal_separator}\d{{2}}", r"\d{4}"],
            )
            if value:
                salary["monthly"] = value

    #Conversion
    if list(salary.keys()) == ["annual"]:
        salary["monthly"] = int(salary["annual"] / conversion_rate)
    elif list(salary.keys()) == ["monthly"]:
        salary["annual"] = int(salary["monthly"] * conversion_rate)

    if not salary: #perhaps could be that salary is 0
        return None
    return salary


def salary_from_description(
    text,
    regexes: Sequence[str] = DEFAULT_DESCRIPTION_REGEXES,
    method: Callable = salary_from_text,
    **kwargs,
):
    """Find salary content in text using regex sections."""
    if not isinstance(text, str):
        return None
    for regex in regexes:
        salary_section = re.search(regex, text, flags=re.IGNORECASE)
        if salary_section:
            salary = method(salary_section.group(), **kwargs)
            return salary
    return None
