"""Raw acquisition for one explicit query scope; no profile selection."""

from jobscraping.acquisition.collector import failure_message, run_collection
from jobscraping.config.models import CollectionConfig
from jobscraping.pipelines.collecting import (
    KEYWORDS,
    RANKINGS,
    SALARY_BEARABLE,
    SCRAPERS,
    build_scraper,
    validate_postings_quality,
)
from jobscraping.pipelines.store_universal import (
    load_postings,
    save_incomplete_run,
    store_universal_postings,
)
from jobscraping.processing.postings_utils import factual_postings, validate_cache_mode


def run_universal_scrape_flow(
    path, scrapers=SCRAPERS, keywords=KEYWORDS, cache_mode=None,
    cache_hit_predicate=None, seed_history=None, required_fields_by_source=None,
    minimum_source_retention=None, minimum_field_completeness_by_source=None,
    verbose=False, **kwargs,
):
    """Discover current activity, reuse complete facts, gate quality, then store.

    A legacy profile history can seed factual cache entries once. It is never
    treated as evidence of current activity or as a raw retention baseline.
    """
    validate_cache_mode(cache_mode)
    overrides = {}
    for key, value in kwargs.items():
        if key.endswith("extra_keywords"):
            acquisition_keywords = {field: sorted(set(words)) for field, words in (value or {}).items()
                                    if field in ("titlewords", "locations") and words}
            if acquisition_keywords:
                overrides[key] = acquisition_keywords
        elif key.endswith(("extra_titlewords", "extra_locations")) and value:
            overrides[key] = sorted(set(value))
    scope = {
        "scrapers": sorted(s.__name__ for s in scrapers),
        "titlewords": sorted(set(keywords.get("titlewords", []))),
        "locations": sorted(set(keywords.get("locations", []))),
        "overrides": overrides,
    }
    previous = load_postings(path, "current_postings.json")
    same_scope = scope == load_postings(path, "collection_scope.json")
    cache = load_postings(path, "postings_history.json")
    if not cache:
        cache = {k: p for k, p in (seed_history or {}).items()
                 if all(p.get(f) for f in ("title", "company", "description"))}
    scraper_defaults = {
        "rankings": kwargs.pop("rankings", RANKINGS),
        "salary_bearable": kwargs.pop("salary_bearable", SALARY_BEARABLE),
    }
    adapters = [build_scraper(scraper_class, keywords=keywords, **scraper_defaults, **kwargs)
                for scraper_class in scrapers]
    config = CollectionConfig(
        sites=tuple(adapter.source for adapter in adapters),
        queries=tuple(sorted(set(keywords.get("titlewords", [])))),
        locations=tuple(keywords.get("locations", [])),
        steps=(),
        overrides=overrides,
        cache_mode=cache_mode,
        cached_postings=factual_postings(cache),
        cache_hit_predicate=cache_hit_predicate,
    )
    result = run_collection(adapters, config, artifact_path=path)
    raw = factual_postings(result["records"])
    if result["report"]["failed"]:
        error = RuntimeError(failure_message(result["report"]))
        save_incomplete_run(raw, path, error)
        raise error
    try:
        required_fields = {p.get("source"): ("title", "description", "company") for p in raw.values()}
        for source, fields in (required_fields_by_source or {}).items():
            required_fields[source] = tuple(set(required_fields.get(source, ())) | set(fields))
        validate_postings_quality(raw, previous_postings=previous if same_scope else {},
            required_fields_by_source=required_fields,
            minimum_source_retention=minimum_source_retention,
            minimum_field_completeness_by_source=minimum_field_completeness_by_source,
            verbose=verbose)
    except ValueError as error:
        save_incomplete_run(raw, path, error)
        raise
    return store_universal_postings(raw, path, scope)
