"""Contract tests for adapter steps (B10).

A test-local runner plays the collector's role so the step contract is proven
without a collector, network, browser or profile. B22 can copy this call shape.
"""

import unittest

from jobscraping.scrapers.steps import Step
from jobscraping.specs.postings import COLLECTED_POSTINGS, DISCOVERED_POSTINGS


def everything(records, config):
    return {key: {**record, "description": "full text"} for key, record in records.items()}


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


def run_steps(adapter, records, config=None, only=None):
    """The collector's call shape: ordered steps, optional selection, no abort."""
    report = {"source": adapter.source, "steps": [], "failed": False}
    for declared in adapter.steps:
        name, run = (declared.name, declared.run) if isinstance(declared, Step) else declared
        if only is not None and name not in only:
            report["steps"].append({"name": name, "status": "skipped"})
            continue
        try:
            records = run(records, config)
        except Exception as error:
            report["failed"] = True
            report["steps"].append({"name": name, "status": "failed", "error": str(error)})
            continue
        report["steps"].append({"name": name, "status": "ok", "records": len(records)})
    if not records:
        report["failed"] = True
    report["records"] = records
    return report


def postings(*ids):
    return {f"one.test{i}": {"source": "one.test", "id": str(i), "url": f"https://one.test/{i}"}
            for i in ids}


class StepContractTest(unittest.TestCase):
    def test_one_step_adapter_runs_in_declared_order(self):
        report = run_steps(DiscoveryOnly, postings(1))
        self.assertEqual([step["name"] for step in report["steps"]], ["all"])
        self.assertEqual(report["records"]["one.test1"]["description"], "full text")
        self.assertFalse(report["failed"])

    def test_two_step_adapter_runs_listing_before_details(self):
        report = run_steps(ListingThenDetails, {})
        self.assertEqual([step["name"] for step in report["steps"]], ["listings", "details"])
        self.assertEqual(len(report["records"]), 1)
        self.assertFalse(report["failed"])

    def test_selection_skips_steps_by_name(self):
        report = run_steps(ListingThenDetails, {}, only=("listings",))
        self.assertEqual([step["status"] for step in report["steps"]], ["ok", "skipped"])
        self.assertNotIn("description", report["records"]["two.test1"])

    def test_raising_step_is_recorded_and_later_steps_still_run(self):
        report = run_steps(FailingDetails, {})
        self.assertEqual(
            [(step["name"], step["status"]) for step in report["steps"]],
            [("listings", "ok"), ("details", "failed"), ("cleanup", "ok")],
        )
        self.assertIn("detail page unavailable", report["steps"][1]["error"])
        self.assertTrue(report["failed"])
        self.assertEqual(len(report["records"]), 1, "a failed step is never empty success")

    def test_zero_records_is_a_failed_acquisition(self):
        report = run_steps(DiscoveryOnly, {})
        self.assertTrue(report["failed"])
        self.assertEqual(report["records"], {})

    def test_declared_specs_describe_the_handoff(self):
        declared = ListingThenDetails.steps[1]
        self.assertIs(declared.input_spec, DISCOVERED_POSTINGS)
        self.assertIs(declared.output_spec, COLLECTED_POSTINGS)
        listed = listings({}, None)
        self.assertEqual(declared.input_spec.check(listed), [])
        collected = declared.run(listed, None)
        self.assertEqual(declared.output_spec.check(collected), [])


if __name__ == "__main__":
    unittest.main()
