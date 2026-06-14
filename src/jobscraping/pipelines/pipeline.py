"""VERY EXPERIMENTAL
Composable pipeline helpers for staged job-posting collection."""

from __future__ import annotations

from typing import Iterable

from methods import outputs, postings_utils
from methods.pipelines import collecting

PIPELINE_STEPS = ("scrape", "filter", "store", "output")


def scrape_step(**kwargs):
    """Run only the scraping stage and return raw postings."""
    return collecting.scrape_sites(**kwargs)


def filter_step(postings, **kwargs):
    """Apply filter/ranking transformations to postings."""
    return postings_utils.process_data(postings, **kwargs)


def store_step(**kwargs):
    """Run the collection and storage stage."""
    return collecting.get_postings(**kwargs)


def output_step(results, **kwargs):
    """Generate output artifacts for a posting collection."""
    return outputs.generate_outputs(results, **kwargs)


def run_pipeline(steps: Iterable[str] = PIPELINE_STEPS, **kwargs):
    """Run selected pipeline stages in order and return the collected state."""
    state = {}
    steps = tuple(steps)

    if "scrape" in steps:
        state["raw_results"] = scrape_step(**kwargs)

    if "filter" in steps:
        source = state.get("raw_results") if "raw_results" in state else kwargs.get("postings")
        if source is not None:
            state["filtered_results"] = filter_step(source, **kwargs)

    if "store" in steps:
        state["stored_results"] = store_step(**kwargs)

    if "output" in steps:
        source = state.get("stored_results", {})
        results = source.get("results") if isinstance(source, dict) else kwargs.get("results")
        if results is not None:
            state["outputs"] = output_step(results, **kwargs)

    return state
