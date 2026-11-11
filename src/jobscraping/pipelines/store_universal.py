"""Scoped raw storage. Dani query provenance never replaces the root vault."""

from copy import deepcopy
from datetime import date, datetime
from pathlib import Path

from jobscraping.io.files_io import load_file_if_str, save_data
from jobscraping.processing.attributes import merge_matched_titlewords
from jobscraping.processing.postings_utils import factual_postings


UNIVERSAL_POSTINGS_FOLDER = "data/save/postings/universal"


def load_postings(path, filename):
    file = Path(path) / filename
    return load_file_if_str(str(file), "dict") if file.exists() else {}


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
        history[key] = merged
        posting.update(deepcopy(merged))
    return history


def save_incomplete_run(postings, path, error):
    save_data({"error": str(error), "postings": factual_postings(postings)},
              path=str(Path(path)) + "/", name="incomplete_run_" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f"),
              with_timestamp=False)


def store_universal_postings(postings, path, scope):
    """Persist a quality-checked raw collection, including a valid empty run."""
    current = factual_postings(postings)
    previous = factual_postings(load_postings(path, "postings_history.json"))
    added_ids = current.keys() - previous.keys()
    history = merge_observations(current, previous)
    for filename, data in (("current_postings.json", current),
                           ("postings_history.json", history),
                           ("newly_added_postings.json", {k: current[k] for k in added_ids}),
                           ("collection_scope.json", scope)):
        save_data(data, path=str(Path(path)) + "/", name=filename, with_timestamp=False)
    return current
