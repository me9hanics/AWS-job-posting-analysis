"""Transitional re-export shim; detection now lives in ``data.language``.

B44 removes this module once callers import the data layer directly.
"""

from jobscraping.data.language import (
    LanguageEvidence,
    extract_language_requirements,
    guess_required_languages,
)

__all__ = [
    "LanguageEvidence",
    "extract_language_requirements",
    "guess_required_languages",
]
