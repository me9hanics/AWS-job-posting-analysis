"""Helpers for job posting attributes: salary parsing, scoring, keyword analysis."""

import re
from typing import List, Callable, Any, Dict, Sequence


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
    keywords: Dict[str, Sequence[str]] | None = None,
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

def salary_points(
    salary,
    root_value=None,
    salary_ratio=0.15/100,
    high_dropoff=True,
    dropoff_bearable_ratio=1.25, #better at around 1.4
):
    """Calculate salary-based score, with optional dropoff."""
    if not root_value:
        root_value = 5000
    points = (salary - root_value) * salary_ratio
    if high_dropoff & (salary > root_value * dropoff_bearable_ratio):
        max_points = (root_value * dropoff_bearable_ratio - root_value) * salary_ratio
        points = 2 * max_points - points
    return points

def check_locations(locations: List, locations_desired: List):
    """Check if any desired location is present in the given locations list."""
    if locations and locations_desired:
        for location in locations:
            for desired in locations_desired:
                if desired.lower() in location.lower(): #in the string, e.g. "wien" in "wien 04"
                    return True
    return False

def score_text_nested(text: str, rules: dict) -> float:
    """
    Recursively score text based on nested regex pattern rules.

    Parameters:
    text: str
        The text to score.
    rules: dict
        Nested dictionary containing regex patterns and their scores.

    Returns:
    float: The total score for the text.
    """
    score = 0.0
    for _key, value in rules.items():
        if isinstance(value, dict):
            if "patterns" in value:
                flags = value.get("flags", 0)
                for pattern, pts in value["patterns"].items():
                    if re.search(pattern, text, flags=flags):
                        score += pts
            else:
                #Check nested dict
                score += score_text_nested(text, value)
    return score

def rank_postings(
    postings: dict,
    keyword_points=None,
    desc_ratio=0.3,
    root_value=5000,
    salary_ratio=0.15/100,
    dropoff_bearable_ratio=1.4,
    overwrite=True,
    locations_desired: List | None = None,
    locations_secodary: List | None = None,
    **_kwargs,
):
    """
    Rank postings using regex-based scoring system.
    
    Parameters:
    postings: dict
        Dictionary of job postings to rank.
    keyword_points: dict
        Nested dictionary with regex patterns and scores.
    desc_ratio: float
        Ratio to apply to description scores (title gets full weight).
    root_value: int
        Root salary value for scoring.
    salary_ratio: float
        Ratio for salary scoring.
    dropoff_bearable_ratio: float
        Ratio at which salary scoring starts to drop off.
    overwrite: bool
        If True, overwrite existing points.
    locations_desired: list
        List of desired locations.
    locations_secodary: list
        List of secondary locations.
        
    Returns:
    dict: Updated postings with points added.
    """
    if not keyword_points:
        keyword_points = {}

    if locations_desired is None:
        locations_desired = []
    if locations_secodary is None:
        locations_secodary = []

    for posting_id, posting in postings.items():
        if not overwrite and ("points" in posting.keys()) and posting["points"] is not None:
            continue

        title = posting.get("title", "")
        description = posting.get("description", "")
        salary = posting.get("salary_monthly_guessed")

        title_points = score_text_nested(title, keyword_points)
        description_points = score_text_nested(description, keyword_points) * desc_ratio

        points = title_points + description_points
        if salary:
            points += salary_points(
                salary,
                root_value=root_value,
                salary_ratio=salary_ratio,
                high_dropoff=True,
                dropoff_bearable_ratio=dropoff_bearable_ratio,
            )

        if posting.get("locations"):
            if not check_locations(posting["locations"], locations_desired=locations_desired):
                points -= 1
                if not check_locations(posting["locations"], locations_desired=locations_secodary):
                    points -= 1

        postings[posting_id]["points"] = round(points, 2)

    return postings

def find_keywords(
    text: str,
    keywords_list: List[str],
    case_sensitive=False,
    **_kwargs,
) -> List[str]:
    """
    Find keywords in text from a predefined list.
    
    Parameters:
    text: str
        The text to search in.
    keywords_list: list
        List of keywords to search for.
    sort: bool
        If True, return in the order they appear in keywords_list (already sorted by importance).
        
    Returns:
    list: List of matched keywords.
    """
    if not keywords_list:
        return []

    found = []
    if not case_sensitive:
        text = text.lower()

    for keyword in keywords_list:
        if not case_sensitive:
            keyword = keyword.lower()
        if keyword in text:
            found.append(keyword)

    return found

def find_keywords_in_postings(
    postings: dict,
    ordered_keywords: List | Dict,
    overwrite=True,
    sort=True,
    method: Callable[[str, list, list, bool, dict], List[Any]] = find_keywords,
    description_key="description",
    **_kwargs,
):
    """Find keywords inside each posting and store them under the posting dict."""
    if isinstance(ordered_keywords, dict):
        ordered_keywords = list(ordered_keywords.keys())

    case_sensitive_keywords = [
        kw for kw in ordered_keywords if any(c.isupper() for c in kw)
    ]
    case_insensitive_keywords = [
        kw for kw in ordered_keywords if not any(c.isupper() for c in kw)
    ]

    for posting_id, posting in postings.items():
        if overwrite or ("keywords" not in posting.keys()) or (not posting["keywords"]):
            postings[posting_id]["keywords"] = []
            if description_key in posting.keys():
                text = posting[description_key]
                keywords = method(text, keywords_list=case_sensitive_keywords,
                                  case_sensitive=True, sort=sort)
                keywords.extend(
                    method(
                        text,
                        keywords_list=case_insensitive_keywords,
                        case_sensitive=False,
                        sort=sort,
                    )
                )
                # Preserve order while de-duplicating.
                postings[posting_id]["keywords"] = list(dict.fromkeys(keywords))
    return postings

def add_matched_titleword(posting_data, titleword):
    """Add a titleword to a posting, avoiding duplicates."""
    if not titleword:
        return posting_data
    matched = posting_data.get("matched_titlewords")
    if not matched:
        posting_data["matched_titlewords"] = [titleword]
    elif titleword not in matched:
        matched.append(titleword)
    return posting_data

def merge_matched_titlewords(target_posting, incoming_posting):
    """Merge titleword lists between postings, preserving order."""
    incoming_titlewords = incoming_posting.get("matched_titlewords")
    if not incoming_titlewords:
        return
    if not isinstance(incoming_titlewords, list):
        incoming_titlewords = [incoming_titlewords]
    existing_titlewords = target_posting.get("matched_titlewords")
    if not existing_titlewords:
        target_posting["matched_titlewords"] = list(incoming_titlewords)
        return
    for titleword in incoming_titlewords:
        if titleword not in existing_titlewords:
            existing_titlewords.append(titleword)

def analyze_text_language(texts) -> list:
    """Returns a list of 'en', 'de', or None for each text in texts."""
    #Separated string sets and regexes for speed
    english_words = {
        'university', 'course', 'work', 'grade', 'and', 'for', 'with', 'develop', 'implement',
        'design', 'build', 'create', 'product', 'manage', 'lead', 'analyze', 'talk', 'need',
        'presenting', 'creating', 'adding', 'able', 'successful', 'have', 'has', 'had', 'will',
        'would', 'should', 'could', 'good', 'better', 'best', 'great', 'way', 'ways', 'our',
        'your', 'their', 'this', 'that', 'these', 'those', 'are', 'is', 'was', 'were', 'been',
        'being', 'we', 'you', 'they', 'who', 'which', 'what', 'when', 'where', 'some', 'any',
        'many', 'much', 'more', 'most', 'through', 'about', 'into', 'from', 'within', 'provide',
        'support', 'help', 'make', 'take', 'get', 'including', 'such', 'both', 'each', 'other',
        'looking', 'seeking', 'join', 'grow', 'learn'
    }
    german_words = {
        'der', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einem', 'einer', 'eines',
        'und', 'oder', 'aber', 'denn', 'weil', 'dass', 'ist', 'sind', 'war', 'waren', 'wird',
        'werden', 'wurde', 'wurden', 'haben', 'hat', 'hatte', 'hatten', 'abteilung', 'gegen',
        'wart', 'entwickl', 'arbeit', 'implementier', 'optimier', 'automatisier', 'sie', 'ihr',
        'ihre', 'ihren', 'ihrem', 'wir', 'unser', 'unsere', 'für', 'mit', 'zu', 'von', 'aus',
        'bei', 'nach', 'im', 'an', 'auf', 'auch', 'nur', 'schon', 'noch', 'nicht', 'kein',
        'keine', 'durch', 'über', 'unter', 'sehr', 'mehr', 'alle', 'jede', 'jeder', 'suchen',
        'sucht', 'bieten', 'bietet', 'sowie', 'als', 'wenn', 'wann', 'wie', 'was', 'wo'
    }
    english_regex = [
        re.compile(r'\bgrade:\b'),
        re.compile(r'\bpresenting\b'),
        re.compile(r'\bcreating\b'),
        re.compile(r'\badding\b'),
    ]
    german_regex = [
        re.compile(r'abteilung'),
        re.compile(r'gegen'),
        re.compile(r'wart'),
        re.compile(r'\bentwickl'),
        re.compile(r'\barbeit\b'),
        re.compile(r'\bimplementier'),
        re.compile(r'\boptimier'),
        re.compile(r'\bautomatisier'),
    ]
    if ((not isinstance(texts, list)) and (not isinstance(texts, str))) or not texts:
        return []
    if isinstance(texts, str):
        texts = [texts]
    results = []
    for text in texts:
        english_count = 0
        german_count = 0
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        english_count += len(words & english_words)
        german_count += len(words & german_words)
        for pattern in english_regex:
            if pattern.search(text_lower):
                english_count += 1
        for pattern in german_regex:
            if pattern.search(text_lower):
                german_count += 1
        if english_count > german_count:
            results.append('en')
        elif german_count > english_count:
            results.append('de')
        else:
            results.append(None)
    return results
def analyze_postings_language(
    postings: Dict,
    description_key="description",
    **_kwargs,
) -> Dict:
    """Annotate postings with detected language based on description text."""
    descriptions = [posting.get(description_key, "") for posting in postings.values()]
    languages = analyze_text_language(descriptions)
    for key, lang in zip(postings.keys(), languages):
        postings[key]["language"] = lang
    return postings
