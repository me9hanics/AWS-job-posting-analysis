import re
from typing import List, Callable, Any, Dict, Tuple
from copy import deepcopy

def salary_number_from_str(text, keywords=[],
                           remove_chars = ['.'], lengths=[6,5]):
    if type(text) != str:
        return None
    for char in remove_chars:
        text_cleaned = text.replace(char, "")
    if not keywords:
        for length in lengths:
            #Search for length-digit numbers
            value = re.search(rf'\d{{{length}}}', text_cleaned)
            if value:
                return int(value.group())
    else:
        if any([keyword in text for keyword in keywords]):
            for length in lengths:
                value = re.search(rf'\d{{{length}}}', text_cleaned)
                if value:
                    return int(value.group())
    return None

def salary_regex(text, regexes=[r'\d{6},\d{2}', r'\d{5},\d{2}',  r'\d{6}', r'\d{5}'],
                 decimal_separator=","):
    for regex in regexes:
        value = re.search(regex, text)
        if value:
            try:
                return int(value.group())
            except ValueError:
                return int(float(value.group().replace(decimal_separator,".")))
    return None

def salary_from_text(text, keywords={"annual":["jährlich", "yearly", "per year", "annual", "jährige", "pro jahr", "p.a."],
                                     "monthly":["monatlich", "monthly", "per month", "pro monat"]},
                     clarity_comma_char=".", decimal_separator=",", conversion_rate=12):
    if type(text) != str:
        return None
    text = text.lower()
    salary = {}
    if "annual" in keywords.keys():
        value = salary_number_from_str(text, keywords["annual"], remove_chars=[clarity_comma_char], lengths=[6,5])
        if value:
            salary["annual"] = value
    if (not salary) and ("monthly" in keywords.keys()):
        value = salary_regex(text.replace(clarity_comma_char, ""), decimal_separator=decimal_separator,
                                  regexes=[r'\d{{4}}{0}\d{{2}}'.format(decimal_separator)])
        if not value:
            value = salary_number_from_str(text, keywords["monthly"], remove_chars=[clarity_comma_char], lengths=[4])
        if value:
            salary["monthly"] = value
    if not salary:
        value = salary_regex(text.replace(clarity_comma_char, ""), decimal_separator=decimal_separator,
                                  regexes=[r'\d{{6}}{0}\d{{2}}'.format(decimal_separator), r'\d{{5}}{0}\d{{2}}'.format(decimal_separator), r'\d{6}', r'\d{5}'])
        if value:
            salary["annual"] = value
        else:
            value = salary_regex(text.replace(clarity_comma_char, ""), decimal_separator=decimal_separator,
                                      regexes=[r'\d{{4}}{0}\d{{2}}'.format(decimal_separator), r'\d{4}'])
            if value:
                salary["monthly"] = value
        
    #Conversion
    if list(salary.keys()) == ["annual"]:
        salary["monthly"] = int(salary["annual"]/conversion_rate)
    elif list(salary.keys()) == ["monthly"]:
        salary["annual"] = int(salary["monthly"]*conversion_rate)

    if salary.keys() == []:
        return None
    return salary

def salary_from_description(text,
                            regexes = [r'(Salary|Gehalt|Compensation|Vergütung):.*',
                                       r'\b(Gross|Brutto|Net|Netto)\b:.*',
                                       r'(\d{5}[.,]\d+)(?:(?!\d{5}[.,]?\d*).)*?\b(netto|brutto|gross)\b',#select last such number
                                       r'(\d{2}[.,]\d{3}[.,]\d+)(?:(?!\d{2}[.,]\d{3}[.,]\d*).)*?\b(netto|brutto|gross)\b',
                                       r'(\d{4}[.,]\d+)(?:(?!\d{4}[.,]?\d*).)*?\b(netto|brutto|gross)\b',
                                       r'(\d{1}[.,]\d{3}[.,]\d+)(?:(?!\d{1}[.,]\d{3}[.,]\d*).)*?\b(netto|brutto|gross)\b',
                                       r'(\d{5})(?:(?!\d{5}).)*?\b(netto|brutto|gross)\b',
                                       r'(\d{2}[.,]\d{3})(?:(?!\d{2}[.,]\d{3}).)*?\b(netto|brutto|gross)\b',
                                       r'(\d{5}[.,]\d+)(?:(?!\d{5}[.,]?\d*).)*?\b(net|taxes|tax)\b',
                                       r'(\d{4}[.,]\d+)(?:(?!\d{4}[.,]?\d*).)*?\b(net|taxes|tax)\b',
                                       r'(\d{1}[.,]\d{3})(?:(?!\d{1}[.,]\d{3}).)*?\b(netto|brutto|gross)\b',
                                       r'\d{4,5}[.,]\d{2}',
                                       r'(\d{5})(?:(?!\d{5}).)*?\b(net|taxes|tax)\b',
                                       ],
                            method : Callable = salary_from_text,
                            **kwargs):
    if type(text) != str:
        return None
    for regex in regexes:
        salary_section = re.search(regex, text, flags=re.IGNORECASE)
        if salary_section:
            salary = method(salary_section.group(), **kwargs)
            return salary
    return None

def salary_points(salary, root_value = None, salary_ratio = 0.15/100,
                  high_dropoff = True, dropoff_bearable_ratio = 1.25): #better at around 1.4
    if not root_value:
        root_value = 5000
    points = (salary-root_value)*salary_ratio
    if high_dropoff & (salary > root_value*dropoff_bearable_ratio):
        max_points = (root_value*dropoff_bearable_ratio-root_value)*salary_ratio
        points = 2 * max_points - points
    return points

def check_locations(locations:List, locations_desired:List):
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
    for key, value in rules.items():
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

def rank_postings(postings: dict, keyword_points=None, desc_ratio=0.3,
                  root_value=5000, salary_ratio=0.15/100,
                  dropoff_bearable_ratio=1.4, overwrite=True,
                  locations_desired=[], locations_secodary=[], **kwargs):
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
    
    for id, posting in postings.items():
        if not overwrite and ("points" in posting.keys()) and posting["points"] is not None:
            continue
        
        title = posting.get("title", "")
        description = posting.get("description", "")
        salary = posting.get("salary_monthly_guessed")
        
        # Score title and description using regex-based system
        title_points = score_text_nested(title, keyword_points)
        description_points = score_text_nested(description, keyword_points) * desc_ratio
        
        points = title_points + description_points
        
        # Add salary points
        if salary:
            points += salary_points(salary, root_value=root_value, salary_ratio=salary_ratio,
                                         high_dropoff=True, dropoff_bearable_ratio=dropoff_bearable_ratio)
        
        if posting.get("locations"):
            if not check_locations(posting["locations"], locations_desired=locations_desired):
                points -= 1
                if not check_locations(posting["locations"], locations_desired=locations_secodary):
                    points -= 1
        
        postings[id]["points"] = round(points, 3)
    
    return postings

def find_keywords(text: str, keywords_list: List[str], **kwargs) -> List[str]:
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
    
    text_lower = text.lower()
    found = []
    
    for keyword in keywords_list:
        if keyword.lower() in text_lower:
            found.append(keyword)
    
    return found

def find_keywords_in_postings(postings:dict, ordered_keywords:List | Dict, overwrite = True, sort=True,
                              method: Callable[[str, list, list, bool, dict], List[Any]] = find_keywords,
                              description_key = "description", **kwargs):
    if isinstance(ordered_keywords, dict):
        ordered_keywords = list(ordered_keywords.keys()) #TODO fix
    for id, posting in postings.items():
        if overwrite or ("keywords" not in posting.keys()) or (not posting["keywords"]):
            postings[id]["keywords"] = []
            if description_key in posting.keys():
                text = posting[description_key]
                keywords = method(text, keywords_list=ordered_keywords, sort=sort)
                postings[id]["keywords"] = keywords
    return postings

def analyze_text_language(texts):
    #TODO exact word match instead
    """Returns 'en', 'de', 'mixed', or 'unclear' based on text content"""
    english_patterns = [
        'graduated with honors', 'selected courses:', 'works:', 'grade:', 
        'developed', 'implemented', 'designed', 'built', 'created', 
        'managed', 'led', 'analyzed', 'gave a talk', 'presenting a poster'
    ]
    german_patterns = [
        'für', 'mit', 'der', 'das', 'und', 'über', #'die',
        'von', 'zu', 'bei', 'im', 'abteilung', 'gegenwart'
        'entwicklung', 'zusammenarbeit',
        'implementierung', 'optimierung','automatisierte', 

    ]
    
    english_count = 0
    german_count = 0
    
    for text in texts:
        text_lower = text.lower()
        for pattern in english_patterns:
            if pattern in text_lower:
                english_count += 1
        for pattern in german_patterns:
            if pattern in text_lower:
                german_count += 1
    
    if english_count > 0 and german_count == 0:
        return 'en'
    elif german_count > 0 and english_count == 0:
        return 'de'
    elif english_count > 0 and german_count > 0:
        return 'mixed'
    else:
        return 'unclear'