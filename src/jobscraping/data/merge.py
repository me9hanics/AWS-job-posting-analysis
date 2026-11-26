"""Merge rules for posting observations and the history rebuild."""

from copy import deepcopy
from datetime import date


def _material_changed(old, posting):
    """Only title and description decide a change; absent keys leave stored values."""
    return any(
        (posting.get(field) or "") != (old.get(field) or "")
        for field in ("title", "description")
        if field in posting
    )


def _last_modified_on(old, posting):
    """Date of the observation that last changed the posting's material."""
    if not old or _material_changed(old, posting):
        return posting.get("collected_on")
    return (old.get("last_modified_on") or old.get("last_collected_on")
            or old.get("collected_on") or posting.get("collected_on"))


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


def merge_observations(current, previous):
    """Keep prior IDs and dates, replacing current observations and derived values."""
    history = deepcopy(previous)
    for key, posting in current.items():
        old = previous.get(key, {})
        merged = {**deepcopy(old), **deepcopy(posting)}
        dates = [p.get(field) for p in (old, posting)
                 for field in ("collected_on", "first_collected_on", "last_collected_on")
                 if p.get(field)]
        if dates:
            merged["first_collected_on"] = min(dates)
            merged["last_collected_on"] = max(dates)
            merged["timespan_days"] = (date.fromisoformat(max(dates)) - date.fromisoformat(min(dates))).days
        merge_matched_titlewords(merged, old)
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
