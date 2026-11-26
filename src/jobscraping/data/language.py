"""Deterministic, profile-neutral evidence from English and German skill clauses."""

import re
from dataclasses import dataclass
from itertools import pairwise


@dataclass(frozen=True)
class LanguageEvidence:
    language: str
    clause: str
    status: str
    levels: tuple[str, ...] = ()
    proficiency: str | None = None


LANGUAGE = re.compile(r"\b(german|deutsch(?:kenntnisse|kenntnissen)?|english|englisch(?:kenntnisse|kenntnissen)?)\b", re.IGNORECASE)
LEVEL = re.compile(r"\b[ABC][12]\b", re.IGNORECASE)
NATIVE = (
    r"\b(?:native(?:[- ]level)?(?:\s+speakers?(?:\s+of)?)?|mother[- ]tongue|muttersprach\w*|muttersprache)\s+(?:in\s+)?" + LANGUAGE.pattern
    + "|" + LANGUAGE.pattern + r".{0,60}\b(?:muttersprach\w*|muttersprache|mother[- ]tongue|native[- ](?:level|speaker))\b"
    + "|" + LANGUAGE.pattern + r"\s+(?:is\s+|on a\s+|at\s+|as your\s+)?native\b"
)
PROFICIENCIES = (
    ("native", NATIVE),
    ("fluent", r"\b(?:fluent\w*|flie[ßs]end\w*|verhandlungssicher\w*|negotiation[- ]level|business[- ]fluent)\b"),
    ("very_good", r"\b(?:very good|excellent|proficient|sehr gut\w*|ausgezeichnet\w*|hervorragend\w*)\b"),
    ("good", r"\b(?:good|gut\w*)\b"),
)
LANGUAGE_NAMES = {"de": "German", "en": "English"}
LEVEL_ORDER = ("A1", "A2", "B1", "B2", "C1", "C2")
OPTIONAL = re.compile(r"\b(?:optional|desirable|preferred|advantage\w*|plus|nice[- ]to[- ]have|von vorteil|wünschenswert|erwünscht|idealerweise)\b", re.IGNORECASE)
UNNECESSARY = re.compile(r"\b(?:no|not|kein\w*|nicht)\b.{0,45}\b(?:required|necessary|requirement|erforderlich|notwendig|vorausgesetzt)\b", re.IGNORECASE)
REQUIRED = re.compile(r"\b(?:required|requirement\w*|must|essential|mandatory|erforderlich\w*|voraussetz\w*|notwendig|benötig\w*|bring\w*|verfüg\w*)\b", re.IGNORECASE)


def extract_language_requirements(text: str) -> list[LanguageEvidence]:
    """Keep named-language levels and obligation within their skill clause.

    This deliberately covers common English/German recruiting wording rather
    than attempting a general grammar. Unqualified mentions remain unknown.
    """
    evidence = []
    for sentence in re.split(r"[;.!?\n•]+|\b(?:but|aber)\b", text, flags=re.IGNORECASE):
        # Commas separate independent requirements, except precise minimums
        # such as 'good German, B2 sufficient'.
        clauses = re.split(r",(?!\s*[ABC][12]\b)\s*", sentence, flags=re.IGNORECASE)
        for clause in clauses:
            clause = clause.strip()
            matches = list(LANGUAGE.finditer(clause))
            if not matches:
                continue
            if re.search(r"\b(?:documents?|application|bewerbung|unterlagen)\b", clause, re.IGNORECASE) and not re.search(r"\b(?:skills?|kenntnisse|speak|fluent)\b", clause, re.IGNORECASE):
                continue
            alternatives = set()
            for index, (left, right) in enumerate(pairwise(matches)):
                between = clause[left.end():right.start()]
                if re.search(r"\b(?:or|oder)\b", between, re.IGNORECASE) and not re.search(r"\b(?:and|und)\b", between, re.IGNORECASE):
                    alternatives.update((index, index + 1))
            shared_prefix = clause[:matches[0].start()]
            for i, match in enumerate(matches):
                language = "de" if match.group().lower().startswith(("german", "deutsch")) else "en"
                before = clause[matches[i-1].end() if i else 0:match.start()]
                after = clause[match.end():matches[i+1].start() if i+1 < len(matches) else len(clause)]
                # The modifier after a conjunction belongs to the next language.
                after = re.split(r"\b(?:and|und|sowie)\b", after, maxsplit=1, flags=re.IGNORECASE)[0]
                before = re.split(r"\b(?:and|und|sowie)\b", before, flags=re.IGNORECASE)[-1] if i else before
                if i and not re.search(r"\w", before):
                    before = shared_prefix
                local = before + " " + match.group() + " " + after
                if i + 1 < len(matches) and not LEVEL.search(local) and not any(
                    re.search(pattern, local, re.IGNORECASE) for _, pattern in PROFICIENCIES
                ) and re.fullmatch(r"\s*-?\s*(?:and|und|sowie|/|&)\s*", clause[match.end():matches[i+1].start()], re.IGNORECASE):
                    # A trailing shared level/modifier: 'Deutsch und Englisch B2'.
                    after += " " + clause[matches[-1].end():]
                    local = before + " " + match.group() + " " + after
                levels = tuple(dict.fromkeys(level.upper() for level in LEVEL.findall(after)))
                proficiency = next((name for name, pattern in PROFICIENCIES if re.search(pattern, local, re.IGNORECASE)), None)
                # Company names/nationality/product references are not skills.
                if not (levels or proficiency) and re.search(r"^\s+(?:company|employer|market|nationality|product|customers?)\b", after, re.IGNORECASE):
                    continue
                if i in alternatives or OPTIONAL.search(local):
                    status = "optional"
                elif UNNECESSARY.search(local) or (UNNECESSARY.search(clause) and len(matches) == 1):
                    status = "unnecessary"
                elif levels or proficiency or REQUIRED.search(clause) or re.search(r"kenntnisse|\b(?:skills?|knowledge|speak)\b", local, re.IGNORECASE):
                    status = "required"
                else:
                    status = "unknown"
                evidence.append(LanguageEvidence(language, clause, status, levels, proficiency))
    return evidence


def guess_required_languages(text: str) -> dict[str, str]:
    """Return the strongest stated German/English requirement, German first."""
    guesses = {}
    for language in ("de", "en"):
        required = [
            evidence for evidence in extract_language_requirements(text)
            if evidence.language == language and evidence.status == "required"
        ]
        if not required:
            continue
        levels = [level for evidence in required for level in evidence.levels]
        if levels:
            guesses[LANGUAGE_NAMES[language]] = max(levels, key=LEVEL_ORDER.index)
            continue
        proficiency = next(
            (name for name in ("native", "fluent", "very_good", "good")
             if any(evidence.proficiency == name for evidence in required)),
            None,
        )
        guesses[LANGUAGE_NAMES[language]] = proficiency or "required"
    return guesses


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
