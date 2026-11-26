"""Derive Dani candidates and outputs from supplied facts, without scraping."""

from copy import deepcopy
from datetime import datetime
from pathlib import Path
import re

from jobscraping.config import configs
from jobscraping.config.constants import (
    CURRENT_POSTINGS_FILENAME, NEWLY_ADDED_POSTINGS_FILENAME, POSTINGS_HISTORY_FILENAME,
)
from jobscraping.data.load import load_postings
from jobscraping.data.merge import merge_observations
from jobscraping.io import files_io
from jobscraping.processing.attributes import analyze_postings_language, analyze_text_language, find_keywords_in_postings, rank_postings
from jobscraping.processing.language_requirements import guess_required_languages
from jobscraping.processing.postings_utils import factual_postings, get_added_and_removed
from jobscraping.processing.transformations import apply_filters_transformations
from jobscraping.profiles.dani import DANI_NON_VIENNA_PENALTY, DANI_PHRASES, DANI_KEYWORD_SCORING, DANI_SALARY_BEARABLE, assess_language, is_candidate, role_contributions, title_excluded
from jobscraping.utils.datastruct_utils import sort_dict_by_key


def derive_profile_postings(
    raw_postings, path, keywords=DANI_PHRASES, rankings=DANI_KEYWORD_SCORING,
    salary_bearable=DANI_SALARY_BEARABLE, threshold=0.01, previous_history=None,
    current_postings_filename=CURRENT_POSTINGS_FILENAME,
    newly_added_postings_filename=NEWLY_ADDED_POSTINGS_FILENAME,
    postings_history_filename=POSTINGS_HISTORY_FILENAME,
    only_thresholded_stored=False, efficient_storing=True, transformations=None,
    language_policy=None, locations_primary=None, locations_secondary=None,
    **kwargs,
):
    """Compare candidates to full history before merge; select only at output.

    Known reappearances and score-driven entrants stay out of newly added.
    Current/newly-added artifacts keep the established pre-threshold ordering.
    """
    path = str(Path(path)) + "/"
    Path(path).mkdir(parents=True, exist_ok=True)
    if previous_history is None:
        previous_file = postings_history_filename
        if not previous_file or not (Path(path) / previous_file).exists():
            previous_file = files_io.get_filename_from_dir(path, index=-1)
        previous_history = load_postings(path, previous_file) if previous_file else {}
    previous_history = deepcopy(previous_history)
    previous_for_diff = deepcopy(previous_history)
    for posting in previous_for_diff.values():
        if posting.get("points") is None:
            posting["points"] = 0
    candidates = {k: p for k, p in factual_postings(raw_postings).items() if is_candidate(p, keywords)}
    analyze_postings_language(candidates)
    rank_postings(candidates, keyword_points=rankings, root_value=salary_bearable,
                  locations_desired=configs.LOCATIONS_DESIRED if locations_primary is None else locations_primary,
                  locations_secodary=configs.LOCATIONS_SECONDARY if locations_secondary is None else locations_secondary)
    find_keywords_in_postings(candidates, ordered_keywords=keywords.get("description_keywords_order", []))
    for p in candidates.values():
        if p.get("locations") and not any(
            "vienna" in location.lower() or re.search(r"\bwien\b", location, re.I)
            for location in p["locations"]
        ):
            p["points"] = round(p["points"] - DANI_NON_VIENNA_PENALTY, 2)
        p["guessed_required_languages"] = guess_required_languages(
            p.get("title", "") + "\n" + p.get("description", "")
        )
        contributions = role_contributions(p.get("title", ""), p.get("description", ""))
        p["role_families"] = [family for family, value in contributions.items() if value]
        p.update(assess_language(p.get("title", "") + "\n" + p.get("description", ""), p.get("language"), language_policy))
        p["points"] = round(p["points"] + p["language_adjustment"], 2)
        p["profile_excluded"] = title_excluded(p, keywords)
    candidates = dict(sorted(candidates.items(), key=lambda item: item[1]["points"], reverse=True))
    added, removed = get_added_and_removed(candidates, previous_for_diff)
    added = sort_dict_by_key(added, key="points", descending=True) if added else {}
    removed = sort_dict_by_key(removed, key="points", descending=True) if removed else {}
    for p in removed.values():
        # Keep historical points for the established delta threshold, applying
        # today's eligibility even to legacy history without language fields.
        description = p.get("description") or ""
        language = (analyze_text_language(description) or [None])[0]
        p.update(assess_language((p.get("title") or "") + "\n" + description, language, language_policy))
        p["profile_excluded"] = title_excluded(p, keywords)
    history = merge_observations(candidates, previous_history)

    def select(postings):
        selected = {k: p for k, p in postings.items()
                    if not p.get("language_excluded") and not p.get("profile_excluded")
                    and (threshold is None or p.get("points", 0) >= threshold)}
        return apply_filters_transformations(selected, transformations=transformations or [])

    if previous_history and postings_history_filename:
        baseline = Path(path) / ("migration_baseline_" + datetime.now().strftime("%Y-%m-%d") + ".json")
        if not any(Path(path).glob("migration_baseline_*.json")):
            files_io.save_data(previous_history, path=path, name=baseline.name, with_timestamp=False)
    for filename, data in ((current_postings_filename, select(candidates) if only_thresholded_stored else candidates),
                           (postings_history_filename, history),
                           (newly_added_postings_filename, select(added) if only_thresholded_stored else added)):
        if filename:
            files_io.save_data(data, path=path, name=filename, with_timestamp=False)
    if not efficient_storing:
        files_io.save_data(candidates, path=path, name="postings", with_timestamp=True)
    results = select(candidates)
    companies = list(dict.fromkeys(p.get("company") for p in results.values()
                     if any("wien" in loc.lower() or "vienna" in loc.lower() for loc in p.get("locations", []) or [])))
    return {"results": results, "added": select(added), "removed": select(removed),
            "companies": companies, "excel_file_path": None}
