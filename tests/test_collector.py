"""The universal collector: run adapters' declared steps over one record set.

The adapter shapes come from the B10 step contract; here they meet the real
``run_collection`` call. B23 and B25 extend this module.
"""

import json
import tempfile
import unittest
from pathlib import Path

from jobscraping.acquisition.collector import failure_message, run_collection
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


def empty_details(records, config):
    return {}


class ListingsThenEmptyDetails:
    """A later step that returns nothing must not wipe the earlier records."""

    source = "two.test"
    steps = (("listings", listings), ("details", empty_details))


def fetch_everything(records, config):
    """A new site's one step: fetch its complete postings in one response."""
    return {
        "fake.test1": {
            "source": "fake.test",
            "id": "1",
            "url": "https://fake.test/1",
            "description": "fake text",
        }
    }


class FakeNewSite:
    """A new site: one module with a source and its steps."""

    source = "fake.test"
    steps = (Step("all", fetch_everything, output_spec=COLLECTED_POSTINGS),)


ADAPTERS = [FakeNewSite]


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

    def test_requested_step_the_adapter_does_not_declare_is_ignored(self):
        config = CollectionConfig(steps=("listings", "company-list"))
        result = run_collection([ListingThenDetails()], config)

        steps = result["report"]["sites"][0]["steps"]
        self.assertEqual([step["name"] for step in steps], ["listings", "details"])
        self.assertEqual([step["status"] for step in steps], ["ok", "skipped"])

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

    def test_an_empty_later_step_keeps_the_earlier_records(self):
        config = CollectionConfig()
        with tempfile.TemporaryDirectory() as root:
            result = run_collection(
                [ListingsThenEmptyDetails()], config, artifact_path=root
            )

            site = result["report"]["sites"][0]
            self.assertEqual(
                [(step["name"], step["status"]) for step in site["steps"]],
                [("listings", "ok"), ("details", "empty")],
            )
            self.assertTrue(site["failed"])
            self.assertEqual(list(result["records"]), ["two.test1"])
            chunks = sorted((Path(root) / "chunks").rglob("*.json"))
            self.assertEqual(
                [chunk.stem for chunk in chunks], ["listings"], "the empty step writes no chunk"
            )


class FailureMessageTest(unittest.TestCase):
    """The one-line summary the pipeline raises for a failed report."""

    def test_failed_and_empty_steps_are_named_with_their_recorded_error(self):
        report = {
            "sites": [
                {
                    "source": "raiffeisen_international",
                    "failed": True,
                    "steps": [
                        {"name": "listings", "status": "failed",
                         "records": None, "error": "HTTP 410 Gone"},
                        {"name": "details", "status": "empty",
                         "records": 0, "error": None},
                        {"name": "cleanup", "status": "ok",
                         "records": 1, "error": None},
                    ],
                }
            ]
        }

        self.assertEqual(
            failure_message(report),
            "Collection failed: raiffeisen_international listings: HTTP 410 Gone; "
            "raiffeisen_international details: no records",
        )

    def test_a_report_without_failed_steps_falls_back_to_no_records(self):
        self.assertEqual(
            failure_message({"sites": [{"source": "x", "failed": False, "steps": []}]}),
            "Collection failed: no records collected",
        )


def http_gone(records, config):
    raise RuntimeError("HTTP 410 Gone")


class AlwaysGone:
    """A site whose only step fails the way a removed posting page does."""

    source = "gone.test"

    def __init__(self, **_kwargs):
        self.steps = (Step("listings", http_gone),)


class PipelineFailureTest(unittest.TestCase):
    """A failed collection writes its artifacts and leaves the vault untouched."""

    def test_a_failed_run_writes_the_report_and_an_incomplete_run(self):
        from jobscraping.pipelines.scrape_universal import run_universal_scrape_flow

        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(RuntimeError) as caught:
                run_universal_scrape_flow(
                    root,
                    scrapers=[AlwaysGone],
                    keywords={"titlewords": ["sales"], "locations": []},
                )

            self.assertIn("HTTP 410 Gone", str(caught.exception))
            self.assertEqual(len(list(Path(root).glob("incomplete_run_*.json"))), 1)
            self.assertTrue((Path(root) / "run_report.json").exists())
            self.assertFalse((Path(root) / "current_postings.json").exists())
            self.assertFalse((Path(root) / "postings_history.json").exists())


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


class ArtifactTest(unittest.TestCase):
    """The opt-in artifacts: chunks per ok step and one run report."""

    def chunk_file(self, root, config, source, step):
        return Path(root) / "chunks" / config.scope_digest() / source / f"{step}.json"

    def test_skipped_step_has_no_chunk(self):
        config = CollectionConfig(steps=("listings",))
        with tempfile.TemporaryDirectory() as root:
            run_collection([ListingThenDetails()], config, artifact_path=root)

            self.assertTrue(self.chunk_file(root, config, "two.test", "listings").exists())
            self.assertFalse(self.chunk_file(root, config, "two.test", "details").exists())

    def test_empty_step_has_no_chunk(self):
        config = CollectionConfig()
        with tempfile.TemporaryDirectory() as root:
            run_collection([FindsNothing()], config, artifact_path=root)

            self.assertFalse(self.chunk_file(root, config, "empty.test", "listings").exists())

    def test_failed_step_is_named_in_the_report_file(self):
        config = CollectionConfig()
        with tempfile.TemporaryDirectory() as root:
            run_collection([FailingDetails()], config, artifact_path=root)

            report = json.loads(
                (Path(root) / "run_report.json").read_text(encoding="utf-8")
            )
            steps = report["sites"][0]["steps"]
            failed = [step for step in steps if step["status"] == "failed"]
            self.assertEqual([step["name"] for step in failed], ["details"])
            self.assertIn("detail page unavailable", failed[0]["error"])
            self.assertFalse(self.chunk_file(root, config, "two.test", "details").exists())

    def test_rerunning_the_same_unit_replaces_its_chunk(self):
        config = CollectionConfig()
        with tempfile.TemporaryDirectory() as root:
            run_collection([ListingThenDetails()], config, artifact_path=root)
            run_collection([ListingThenDetails()], config, artifact_path=root)

            chunks = sorted((Path(root) / "chunks").rglob("*.json"))
            self.assertEqual(len(chunks), 2, [str(chunk) for chunk in chunks])
            self.assertEqual(
                json.loads(chunks[0].read_text(encoding="utf-8"))["step"], "details"
            )

    def test_each_ok_step_gets_its_own_file_with_source_step_and_records(self):
        config = CollectionConfig()
        with tempfile.TemporaryDirectory() as root:
            result = run_collection([ListingThenDetails()], config, artifact_path=root)

            listings_chunk = json.loads(
                self.chunk_file(root, config, "two.test", "listings").read_text(
                    encoding="utf-8"
                )
            )
            details_chunk = json.loads(
                self.chunk_file(root, config, "two.test", "details").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(listings_chunk["source"], "two.test")
            self.assertEqual(listings_chunk["step"], "listings")
            self.assertEqual(
                listings_chunk["records"],
                {"two.test1": {"source": "two.test", "id": "1", "url": "https://two.test/1"}},
            )
            self.assertEqual(details_chunk["step"], "details")
            self.assertEqual(details_chunk["records"], result["records"])

    def test_report_file_content_matches_the_returned_report(self):
        config = CollectionConfig(sites=("one.test",), queries=("data",))
        with tempfile.TemporaryDirectory() as root:
            result = run_collection([DiscoveryOnly()], config, artifact_path=root)

            report = json.loads(
                (Path(root) / "run_report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report, result["report"])


class IntegrationTest(unittest.TestCase):
    """End-to-end runs of ``run_collection`` with a temporary artifact path."""

    def chunk_files(self, root):
        return sorted((Path(root) / "chunks").rglob("*.json"))

    def test_a_one_shot_and_a_two_step_adapter_run_together(self):
        config = CollectionConfig(sites=("one.test", "two.test"))
        with tempfile.TemporaryDirectory() as root:
            result = run_collection(
                [DiscoveryOnly(), ListingThenDetails()], config, artifact_path=root
            )

            self.assertEqual(
                set(result["records"]),
                {"one.test1", "two.test1"},
            )
            self.assertEqual(result["records"]["one.test1"]["description"], "full text")
            self.assertEqual(
                result["records"]["two.test1"]["description"], "detail text"
            )
            sites = result["report"]["sites"]
            self.assertEqual([site["source"] for site in sites], ["one.test", "two.test"])
            self.assertEqual(
                [[step["status"] for step in site["steps"]] for site in sites],
                [["ok"], ["ok", "ok"]],
            )
            self.assertFalse(result["report"]["failed"])
            self.assertFalse(result["report"]["zero_records"])
            steps = [chunk.stem for chunk in self.chunk_files(root)]
            self.assertEqual(
                steps, ["all", "details", "listings"], "one chunk per ok step"
            )
            report = json.loads(
                (Path(root) / "run_report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report, result["report"])

    def test_skipping_details_keeps_partial_records_and_writes_no_details_chunk(self):
        config = CollectionConfig(steps=("listings",))
        with tempfile.TemporaryDirectory() as root:
            result = run_collection([ListingThenDetails()], config, artifact_path=root)

            record = result["records"]["two.test1"]
            self.assertEqual(record["url"], "https://two.test/1")
            self.assertNotIn("description", record, "details never ran")
            site = result["report"]["sites"][0]
            self.assertEqual(
                [(step["name"], step["status"]) for step in site["steps"]],
                [("listings", "ok"), ("details", "skipped")],
            )
            chunked_steps = [chunk.stem for chunk in self.chunk_files(root)]
            self.assertEqual(chunked_steps, ["listings"], "a skipped step writes no chunk")
            self.assertTrue((Path(root) / "run_report.json").exists())

    def test_a_raising_step_names_its_error_and_other_adapters_records_survive(self):
        with tempfile.TemporaryDirectory() as root:
            result = run_collection(
                [DiscoveryOnly(), FailingDetails()],
                CollectionConfig(),
                artifact_path=root,
            )

            failed_site = result["report"]["sites"][1]
            self.assertEqual(
                [(step["name"], step["status"]) for step in failed_site["steps"]],
                [("listings", "ok"), ("details", "failed"), ("cleanup", "ok")],
                "a raising step does not stop later steps",
            )
            self.assertIn("detail page unavailable", failed_site["steps"][1]["error"])
            self.assertIn(
                "one.test1", result["records"], "a healthy adapter keeps its records"
            )
            report = json.loads(
                (Path(root) / "run_report.json").read_text(encoding="utf-8")
            )
            failed = [
                step
                for site in report["sites"]
                for step in site["steps"]
                if step["status"] == "failed"
            ]
            self.assertEqual([step["name"] for step in failed], ["details"])
            self.assertIn("detail page unavailable", failed[0]["error"])

    def test_an_adapter_that_returns_nothing_is_zero_records_and_failed(self):
        with tempfile.TemporaryDirectory() as root:
            result = run_collection(
                [FindsNothing()], CollectionConfig(), artifact_path=root
            )

            self.assertTrue(result["report"]["zero_records"])
            self.assertTrue(result["report"]["failed"])
            self.assertEqual(result["records"], {})
            self.assertEqual(
                result["report"]["sites"][0]["steps"][0]["status"], "empty"
            )

    def test_a_new_site_runs_through_the_same_call_with_one_registry_entry(self):
        adapters = [adapter() for adapter in ADAPTERS]
        with tempfile.TemporaryDirectory() as root:
            result = run_collection(adapters, CollectionConfig(), artifact_path=root)

            self.assertEqual(
                result["records"]["fake.test1"]["description"], "fake text"
            )
            site = result["report"]["sites"][0]
            self.assertEqual(site["source"], "fake.test")
            self.assertEqual(
                [(step["name"], step["status"]) for step in site["steps"]],
                [("all", "ok")],
            )
            self.assertFalse(result["report"]["failed"])
            self.assertEqual(
                [chunk.stem for chunk in self.chunk_files(root)], ["all"]
            )


if __name__ == "__main__":
    unittest.main()
