"""Merge rules for posting observations and the history rebuild."""

from copy import deepcopy
from datetime import date

# A field belongs to exactly one group; anything unlisted is an observed fact.
DERIVED_FIELDS = ("language", "guessed_required_languages",
                  "salary_guessed", "salary_monthly_guessed")
ALWAYS_FRESH_FIELDS = ("collected_on", "date", "isActive", "url")
MERGE_OWNED_FIELDS = ("first_collected_on", "last_collected_on",
                      "timespan_days", "last_modified_on")
PROVENANCE_FIELDS = ("matched_titlewords",)


def has_value(value):
    """An empty observation means "not reported", not "erased"."""
    return value is not None and value != "" and value != [] and value != {}


def _material_changed(old, posting):
    """Only a non-empty title or description can change a posting's material."""
    return any(
        has_value(posting[field])
        and (posting[field] or "") != (old.get(field) or "")
        for field in ("title", "description")
        if field in posting
    )


def _last_modified_on(old, posting):
    """Date of the observation that last changed the posting's material."""
    if not old or _material_changed(old, posting):
        return posting.get("collected_on")
    return (old.get("last_modified_on") or old.get("last_collected_on")
            or old.get("collected_on") or posting.get("collected_on"))


def _as_titleword_list(value):
    """Normalise a titleword observation to a list; empty input stays empty."""
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [value]


def merge_matched_titlewords(target_posting, incoming_posting):
    """Merge titleword lists between postings, preserving order."""
    incoming_titlewords = _as_titleword_list(incoming_posting.get("matched_titlewords"))
    if not incoming_titlewords:
        return
    existing_titlewords = target_posting.get("matched_titlewords")
    if not existing_titlewords:
        target_posting["matched_titlewords"] = list(incoming_titlewords)
        return
    for titleword in incoming_titlewords:
        if titleword not in existing_titlewords:
            existing_titlewords.append(titleword)


def _merge_fields(old, posting):
    """Apply the grouped merge rule to one record, excluding merge-owned dates."""
    merged = deepcopy(old)
    for field, value in posting.items():
        if field in MERGE_OWNED_FIELDS or field in PROVENANCE_FIELDS:
            continue
        if field in ALWAYS_FRESH_FIELDS or field in DERIVED_FIELDS or has_value(value):
            merged[field] = deepcopy(value)
    incoming_titlewords = _as_titleword_list(posting.get("matched_titlewords"))
    if incoming_titlewords:
        merged["matched_titlewords"] = deepcopy(incoming_titlewords)
    merge_matched_titlewords(merged, old)
    return merged


def merge_observations(current, previous):
    """Keep prior IDs and dates, replacing current observations and derived values."""
    history = deepcopy(previous)
    for key, posting in current.items():
        old = previous.get(key, {})
        merged = _merge_fields(old, posting)
        dates = [p.get(field) for p in (old, posting)
                 for field in ("collected_on", "first_collected_on", "last_collected_on")
                 if p.get(field)]
        if dates:
            merged["first_collected_on"] = min(dates)
            merged["last_collected_on"] = max(dates)
            merged["timespan_days"] = (date.fromisoformat(max(dates)) - date.fromisoformat(min(dates))).days
        modified_on = _last_modified_on(old, posting)
        if modified_on:
            merged["last_modified_on"] = modified_on
        else:
            merged.pop("last_modified_on", None)
        history[key] = merged
        posting.update(deepcopy(merged))
    return history


def rebuild_history(current, previous):
    """Merge current observations into history; return (history, newly added)."""
    history = merge_observations(current, previous)
    added = {key: posting for key, posting in current.items() if key not in previous}
    return history, added
