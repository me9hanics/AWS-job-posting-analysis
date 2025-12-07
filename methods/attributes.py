import re
from typing import List
from typing import Callable

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
                            **kwargs):
    if type(text) != str:
        return None
    for regex in regexes:
        salary_section = re.search(regex, text, flags=re.IGNORECASE)
        if salary_section:
            salary = salary_from_text(salary_section.group(), **kwargs)
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

def rank_postings(postings:dict, keyword_points:dict, desc_ratio = 0.3,
                  root_value = None, salary_ratio = 0.15/100,
                  dropoff_bearable_ratio = 1.4, overwrite = True,
                  locations_desired=[], locations_secodary=[], **kwargs):
    for id, posting in postings.items():
        if not overwrite and ("points" in posting.keys()) and posting["points"] is not None:
            continue
        title = posting["title"] if "title" in posting.keys() else ""
        description = posting["description"] if "description" in posting.keys() else ""
        salary = posting["salary_monthly_guessed"]
        points = 0
        title_max_point = 0
        for keyword, value in keyword_points["ranking_lowercase"].items():
            if keyword in title.lower():
                title_max_point = value if abs(value) > abs(title_max_point) else title_max_point
            if keyword in description.lower():
                points += value*desc_ratio
        for keyword, value in keyword_points["ranking_case_sensitive"].items():
            if keyword in title:
                title_max_point = value if abs(value) > abs(title_max_point) else title_max_point
            if keyword in description:
                points += value*desc_ratio
        points += title_max_point

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

def find_keywords(text, non_capital = [], capital = [], sort=True, rankings:dict = None):
    found = []
    for keyword in non_capital:
        if keyword in text.lower():
            found.append(keyword)
    for keyword in capital:
        if keyword in text:
            found.append(keyword)

    if sort:
        found = sorted(found,
            key=lambda k: -abs(rankings.get("ranking_lowercase", {}).get(k, 0))
        )
    return found

def find_keywords_in_postings(postings:dict, non_capital = [], capital=[], overwrite = True, sort=True,
                              method: Callable = find_keywords, description_key = "description",
                              rankings = None, **kwargs):
    for id, posting in postings.items():
        if overwrite or ("keywords" not in posting.keys()) or (not posting["keywords"]):
            postings[id]["keywords"] = []
            if description_key in posting.keys():
                text = posting[description_key]
                keywords = method(text, non_capital=non_capital, capital=capital,
                                              sort=sort, rankings=rankings)
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