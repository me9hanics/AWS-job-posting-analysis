"""Scoped raw storage. Dani query provenance never replaces the root vault."""

from datetime import datetime

from jobscraping.data.load import load_postings, save_json, save_posting_set
from jobscraping.data.merge import rebuild_history
from jobscraping.processing.postings_utils import factual_postings

UNIVERSAL_POSTINGS_FOLDER = "data/save/postings/universal"


def save_incomplete_run(postings, path, error):
    save_json({"error": str(error), "postings": factual_postings(postings)},
              path, "incomplete_run_" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f"),
              with_timestamp=False)


def store_universal_postings(postings, path, scope):
    """Persist a quality-checked raw collection, including a valid empty run."""
    current = factual_postings(postings)
    previous = factual_postings(load_postings(path, "postings_history.json"))
    history, added = rebuild_history(current, previous)
    save_posting_set(history, path, "postings_history.json")
    save_posting_set(current, path, "current_postings.json")
    save_posting_set(added, path, "newly_added_postings.json")
    save_json(scope, path, "collection_scope.json")
    return current
