"""Deterministic, profile-neutral evidence from English and German skill clauses."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageEvidence:
    language: str
    clause: str
    status: str
    levels: tuple[str, ...] = ()
    proficiency: str | None = None


LANGUAGE = re.compile(r"\b(german|deutsch(?:kenntnisse|kenntnissen)?|english|englisch(?:kenntnisse|kenntnissen)?)\b", re.I)
LEVEL = re.compile(r"\b[ABC][12]\b", re.I)
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
OPTIONAL = re.compile(r"\b(?:optional|desirable|preferred|advantage\w*|plus|nice[- ]to[- ]have|von vorteil|wünschenswert|erwünscht|idealerweise)\b", re.I)
UNNECESSARY = re.compile(r"\b(?:no|not|kein\w*|nicht)\b.{0,45}\b(?:required|necessary|requirement|erforderlich|notwendig|vorausgesetzt)\b", re.I)
REQUIRED = re.compile(r"\b(?:required|requirement\w*|must|essential|mandatory|erforderlich\w*|voraussetz\w*|notwendig|benötig\w*|bring\w*|verfüg\w*)\b", re.I)


def extract_language_requirements(text: str) -> list[LanguageEvidence]:
    """Keep named-language levels and obligation within their skill clause.

    This deliberately covers common English/German recruiting wording rather
    than attempting a general grammar. Unqualified mentions remain unknown.
    """
    evidence = []
    for sentence in re.split(r"[;.!?\n•]+|\b(?:but|aber)\b", text, flags=re.I):
        # Commas separate independent requirements, except precise minimums
        # such as 'good German, B2 sufficient'.
        clauses = re.split(r",(?!\s*[ABC][12]\b)\s*", sentence, flags=re.I)
        for clause in clauses:
            clause = clause.strip()
            matches = list(LANGUAGE.finditer(clause))
            if not matches:
                continue
            if re.search(r"\b(?:documents?|application|bewerbung|unterlagen)\b", clause, re.I) and not re.search(r"\b(?:skills?|kenntnisse|speak|fluent)\b", clause, re.I):
                continue
            alternatives = set()
            for index, (left, right) in enumerate(zip(matches, matches[1:])):
                between = clause[left.end():right.start()]
                if re.search(r"\b(?:or|oder)\b", between, re.I) and not re.search(r"\b(?:and|und)\b", between, re.I):
                    alternatives.update((index, index + 1))
            shared_prefix = clause[:matches[0].start()]
            for i, match in enumerate(matches):
                language = "de" if match.group().lower().startswith(("german", "deutsch")) else "en"
                before = clause[matches[i-1].end() if i else 0:match.start()]
                after = clause[match.end():matches[i+1].start() if i+1 < len(matches) else len(clause)]
                # The modifier after a conjunction belongs to the next language.
                after = re.split(r"\b(?:and|und|sowie)\b", after, maxsplit=1, flags=re.I)[0]
                before = re.split(r"\b(?:and|und|sowie)\b", before, flags=re.I)[-1] if i else before
                if i and not re.search(r"\w", before):
                    before = shared_prefix
                local = before + " " + match.group() + " " + after
                if i + 1 < len(matches) and not LEVEL.search(local) and not any(
                    re.search(pattern, local, re.I) for _, pattern in PROFICIENCIES
                ) and re.fullmatch(r"\s*-?\s*(?:and|und|sowie|/|&)\s*", clause[match.end():matches[i+1].start()], re.I):
                    # A trailing shared level/modifier: 'Deutsch und Englisch B2'.
                    after += " " + clause[matches[-1].end():]
                    local = before + " " + match.group() + " " + after
                levels = tuple(dict.fromkeys(level.upper() for level in LEVEL.findall(after)))
                proficiency = next((name for name, pattern in PROFICIENCIES if re.search(pattern, local, re.I)), None)
                # Company names/nationality/product references are not skills.
                if not (levels or proficiency) and re.search(r"^\s+(?:company|employer|market|nationality|product|customers?)\b", after, re.I):
                    continue
                if i in alternatives or OPTIONAL.search(local):
                    status = "optional"
                elif UNNECESSARY.search(local) or (UNNECESSARY.search(clause) and len(matches) == 1):
                    status = "unnecessary"
                elif levels or proficiency or REQUIRED.search(clause) or re.search(r"kenntnisse|\b(?:skills?|knowledge|speak)\b", local, re.I):
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
