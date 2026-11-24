"""The posting data specs, one per pipeline step.

Field names follow the current pipeline (`RAW_POSTING_FIELDS`, the universal
store and derivation); required fields are identity and URL only. Completeness
of the rest is a quality-gate setting per source.
"""

from jobscraping.specs.base import DataSpec, FieldSpec


SOURCE = FieldSpec("source", "str", required=True, produced_by="listings")
ID = FieldSpec("id", "str", required=True, produced_by="listings")
URL = FieldSpec("url", "str", required=True, produced_by="listings")

DISCOVERED_POSTINGS = DataSpec(
    name="discovered_postings",
    key=("source", "id"),
    fields=(
        SOURCE,
        ID,
        URL,
        FieldSpec("title", "str", produced_by="listings"),
        FieldSpec("company", "str", produced_by="listings"),
        FieldSpec("locations", "list", produced_by="listings"),
        FieldSpec("collected_on", "date", produced_by="listings"),
        FieldSpec("date", "date", produced_by="listings"),
        FieldSpec("isActive", "bool", produced_by="listings"),
    ),
)

COLLECTED_POSTINGS = DataSpec(
    name="collected_postings",
    key=("source", "id"),
    fields=(
        SOURCE,
        ID,
        URL,
        FieldSpec("title", "str", produced_by="details"),
        FieldSpec("company", "str", produced_by="details"),
        FieldSpec("description", "str", produced_by="details"),
        FieldSpec("collected_on", "date", produced_by="listings"),
        FieldSpec("date", "date", produced_by="details"),
        FieldSpec("salary", "str", produced_by="details"),
        FieldSpec("salary_guessed", "dict", produced_by="details"),
        FieldSpec("salary_monthly_guessed", "float", produced_by="details"),
        FieldSpec("locations", "list", produced_by="details"),
        FieldSpec("isActive", "bool", produced_by="listings"),
        FieldSpec("isHomeOffice", "bool", produced_by="details"),
        FieldSpec("employmentTypes", "list", produced_by="details"),
        FieldSpec("snippet", "str", produced_by="listings"),
        FieldSpec("role", "str", produced_by="details"),
        FieldSpec("requirements", "any", produced_by="details"),
        FieldSpec("nice_to_have", "any", produced_by="details"),
        FieldSpec("benefits", "any", produced_by="details"),
    ),
)

UNIVERSAL_POSTINGS = DataSpec(
    name="universal_postings",
    key=("source", "id"),
    fields=(
        SOURCE,
        ID,
        URL,
        FieldSpec("title", "str", produced_by="collection"),
        FieldSpec("company", "str", produced_by="collection"),
        FieldSpec("description", "str", produced_by="collection"),
        FieldSpec("salary", "str", produced_by="collection"),
        FieldSpec("salary_guessed", "dict", produced_by="collection"),
        FieldSpec("salary_monthly_guessed", "float", produced_by="collection"),
        FieldSpec("locations", "list", produced_by="collection"),
        FieldSpec("first_collected_on", "date", produced_by="store"),
        FieldSpec("last_collected_on", "date", produced_by="store"),
        FieldSpec("collected_on", "date", produced_by="collection"),
        FieldSpec("timespan_days", "int", produced_by="store"),
        FieldSpec("matched_titlewords", "list", produced_by="collection"),
        FieldSpec("language", "str", produced_by="enrichment"),
        FieldSpec("guessed_required_languages", "dict", produced_by="enrichment"),
        FieldSpec("date", "date", produced_by="collection"),
        FieldSpec("isActive", "bool", produced_by="collection"),
        FieldSpec("isHomeOffice", "bool", produced_by="collection"),
        FieldSpec("employmentTypes", "list", produced_by="collection"),
        FieldSpec("snippet", "str", produced_by="collection"),
        FieldSpec("role", "str", produced_by="collection"),
        FieldSpec("requirements", "any", produced_by="collection"),
        FieldSpec("nice_to_have", "any", produced_by="collection"),
        FieldSpec("benefits", "any", produced_by="collection"),
        FieldSpec("last_modified_on", "date", produced_by="store"),
    ),
)

SCORED_FIELDS = (
    SOURCE,
    ID,
    FieldSpec("points", "float", required=True, produced_by="derivation"),
    FieldSpec("language", "str", produced_by="enrichment"),
    FieldSpec("matched_titlewords", "list", produced_by="collection"),
    FieldSpec("keywords", "list", produced_by="derivation"),
    FieldSpec("role_families", "list", produced_by="derivation"),
    FieldSpec("guessed_required_languages", "dict", produced_by="enrichment"),
    FieldSpec("language_adjustment", "float", produced_by="derivation"),
    FieldSpec("language_excluded", "bool", produced_by="derivation"),
    FieldSpec("profile_excluded", "bool", produced_by="derivation"),
)

SCORED_POSTINGS = DataSpec(
    name="scored_postings",
    key=("source", "id"),
    fields=SCORED_FIELDS,
)

SELECTED_POSTINGS = DataSpec(
    name="selected_postings",
    key=("source", "id"),
    fields=SCORED_FIELDS,
)
