"""The universal collector: run adapters' declared steps over one record set.

The adapter shapes come from the B10 step contract; here they meet the real
``run_collection`` call. B23 and B25 extend this module.
"""

import unittest

from jobscraping.acquisition.collector import run_collection
from jobscraping.config.models import CollectionConfig
from jobscraping.scrapers.steps import Step
from jobscraping.specs.postings import COLLECTED_POSTINGS, DISCOVERED_POSTINGS


def everything(records, config):
    """One-step site: the fetch returns complete postings in one response."""
    return {
        "one.test1": {
            "source": "one.test",
            "id": "1",
            "url": "https://one.test/1",
            "description": "full text",
        }
    }


class DiscoveryOnly:
    """One-shot shape: a site that returns everything in one response."""

    source = "one.test"
    steps = (Step("all", everything, output_spec=COLLECTED_POSTINGS),)


def listings(records, config):
    return {"two.test1": {"source": "two.test", "id": "1", "url": "https://two.test/1"}}


def details(records, config):
    return {key: {**record, "description": "detail text"} for key, record in records.items()}


class ListingThenDetails:
    """Two-step shape, written as a plain pair plus a Step."""

    source = "two.test"
    steps = (
        ("listings", listings),
        Step("details", details, input_spec=DISCOVERED_POSTINGS, output_spec=COLLECTED_POSTINGS),
    )


def failing_details(records, config):
    raise RuntimeError("detail page unavailable")


class FailingDetails:
    """A raising step must not stop later steps from running."""

    source = "two.test"
    steps = (
        ("listings", listings),
        Step("details", failing_details),
        ("cleanup", lambda records, config: records),
    )


def nothing(records, config):
    return {}


class FindsNothing:
    source = "empty.test"
    steps = (("listings", nothing),)


class OneStepTest(unittest.TestCase):
    def test_one_step_adapter_runs_in_declared_order(self):
        result = run_collection([DiscoveryOnly()], CollectionConfig(sites=("one.test",)))

        site = result["report"]["sites"][0]
        self.assertEqual(site["source"], "one.test")
        self.assertEqual([step["name"] for step in site["steps"]], ["all"])
        self.assertEqual(site["steps"][0]["status"], "ok")
        self.assertFalse(site["failed"])
        self.assertFalse(result["report"]["failed"])
        self.assertFalse(result["report"]["zero_records"])

    def test_report_carries_the_scope_digest_and_merged_records(self):
        config = CollectionConfig(sites=("one.test",), queries=("data",))
        result = run_collection([DiscoveryOnly()], config)

        self.assertEqual(result["report"]["scope_digest"], config.scope_digest())
        self.assertEqual(list(result["records"]), ["one.test1"])
        self.assertEqual(
            set(result["report"]), {"scope_digest", "sites", "failed", "zero_records"}
        )


class TwoStepTest(unittest.TestCase):
    def test_two_step_adapter_runs_listing_before_details(self):
        result = run_collection([ListingThenDetails()], CollectionConfig())

        site = result["report"]["sites"][0]
        self.assertEqual([step["name"] for step in site["steps"]], ["listings", "details"])
        self.assertEqual([step["status"] for step in site["steps"]], ["ok", "ok"])
        self.assertEqual(site["steps"][1]["records"], 1)
        self.assertEqual(result["records"]["two.test1"]["description"], "detail text")
        self.assertFalse(result["report"]["failed"])

    def test_selection_skips_steps_by_name(self):
        config = CollectionConfig(steps=("listings",))
        result = run_collection([ListingThenDetails()], config)

        site = result["report"]["sites"][0]
        self.assertEqual([step["status"] for step in site["steps"]], ["ok", "skipped"])
        self.assertIsNone(site["steps"][1]["records"])
        self.assertNotIn("description", result["records"]["two.test1"])

    def test_requested_step_the_adapter_does_not_declare_is_skipped(self):
        config = CollectionConfig(steps=("listings", "company-list"))
        result = run_collection([ListingThenDetails()], config)

        steps = result["report"]["sites"][0]["steps"]
        self.assertEqual([step["name"] for step in steps], ["listings", "details", "company-list"])
        self.assertEqual([step["status"] for step in steps], ["ok", "skipped", "skipped"])

    def test_raising_step_is_recorded_and_later_steps_still_run(self):
        result = run_collection([FailingDetails()], CollectionConfig())

        site = result["report"]["sites"][0]
        self.assertEqual(
            [(step["name"], step["status"]) for step in site["steps"]],
            [("listings", "ok"), ("details", "failed"), ("cleanup", "ok")],
        )
        self.assertIn("detail page unavailable", site["steps"][1]["error"])
        self.assertTrue(site["failed"])
        self.assertTrue(result["report"]["failed"])
        self.assertEqual(len(result["records"]), 1, "a failed step never drops the records")


class FailureTest(unittest.TestCase):
    def test_empty_result_is_empty_and_fails_the_adapter(self):
        result = run_collection([FindsNothing()], CollectionConfig())

        site = result["report"]["sites"][0]
        self.assertEqual(site["steps"][0]["status"], "empty")
        self.assertEqual(site["steps"][0]["records"], 0)
        self.assertTrue(site["failed"])
        self.assertTrue(result["report"]["zero_records"])
        self.assertTrue(result["report"]["failed"])
        self.assertEqual(result["records"], {})

    def test_one_empty_site_fails_the_run_but_not_the_records(self):
        result = run_collection([DiscoveryOnly(), FindsNothing()], CollectionConfig())

        self.assertEqual([site["failed"] for site in result["report"]["sites"]], [False, True])
        self.assertFalse(result["report"]["zero_records"])
        self.assertTrue(result["report"]["failed"])
        self.assertEqual(len(result["records"]), 1)


class ScopeDigestTest(unittest.TestCase):
    def test_cache_inputs_are_not_scope(self):
        scope = CollectionConfig(sites=("one.test",), queries=("data",), locations=("wien",))
        cached = CollectionConfig(
            sites=("one.test",),
            queries=("data",),
            locations=("wien",),
            cache_mode="reuse",
            cached_postings={"one.test1": {"id": "1"}},
            cache_hit_predicate=lambda source, record, cached: True,
        )
        self.assertEqual(scope.scope_digest(), cached.scope_digest())

    def test_changing_a_scope_field_changes_the_digest(self):
        base = CollectionConfig(sites=("one.test",), queries=("data",))
        other = CollectionConfig(sites=("one.test",), queries=("platform",))
        self.assertNotEqual(base.scope_digest(), other.scope_digest())

    def test_non_json_override_values_hash_deterministically(self):
        first = CollectionConfig(overrides={"only": {"b", "a"}})
        second = CollectionConfig(overrides={"only": {"a", "b"}})
        self.assertEqual(first.scope_digest(), second.scope_digest())
        self.assertNotEqual(first.scope_digest(), CollectionConfig().scope_digest())


if __name__ == "__main__":
    unittest.main()
