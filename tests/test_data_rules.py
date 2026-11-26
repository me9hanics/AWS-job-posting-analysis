"""Characterization tests for the posting data rules (B04).

These tests lock the behaviour of the code as it is today, not the behaviour
the design document asks for. Fixtures in ``tests/fixtures`` are shared with
B02a and B27 as a parity gate.
"""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from jobscraping.data.merge import merge_observations
from jobscraping.pipelines.store_universal import store_universal_postings
from jobscraping.processing.postings_utils import (
    factual_postings,
    get_added_and_removed,
)
from jobscraping.scrapers import KarriereAT, http

FIXTURES = Path(__file__).with_name("fixtures")

# Profile-only fields: they belong to derivation and must never be stored.
PROFILE_FIELDS = {"points", "keywords", "score", "profile_excluded", "language_excluded"}

# Independent copy of the persisted raw record shape.
EXPECTED_RAW_FIELDS = {
    "title", "company", "description", "source", "salary", "salary_guessed",
    "salary_monthly_guessed", "locations", "first_collected_on", "last_collected_on",
    "collected_on", "timespan_days", "matched_titlewords", "date", "id", "url",
    "isActive", "isHomeOffice", "employmentTypes", "snippet", "role",
    "requirements", "nice_to_have", "benefits", "last_modified_on",
    "language", "guessed_required_languages",
}


def load_fixture(name):
    with open(FIXTURES / name, encoding="utf-8") as file:
        return json.load(file)


def listing(posting_id=1, title="Sales"):
    return {"jobsItem": {
        "id": posting_id, "title": title, "company": {"name": "Company"},
        "locations": [{"name": "Vienna"}], "salary": "", "isActive": True,
        "isHomeOffice": False, "employmentTypes": [],
        "link": f"https://www.karriere.at/jobs/{posting_id}", "snippet": "",
        "date": "2025-03-01",
    }}


def listing_response(items):
    payload = {"data": {"jobsSearchList": {"activeItems": {"items": items}}}}
    return SimpleNamespace(text=json.dumps(payload))


def detail_response(text):
    payload = {"data": {"jobDetailContent": {"jobContent": {"text": text},
                                             "jobHeader": {"job": {"id": 1}}}}}
    return SimpleNamespace(text=json.dumps(payload))


class FactualPostingsTests(unittest.TestCase):
    def setUp(self):
        self.postings = load_fixture("postings_projection.json")
        self.factual = factual_postings(self.postings)

    def test_profile_fields_are_dropped(self):
        for key, posting in self.factual.items():
            with self.subTest(posting=key):
                self.assertTrue(PROFILE_FIELDS.isdisjoint(posting))

    def test_every_raw_posting_field_survives(self):
        posting = {"id": "1", "source": "test"}
        for field in EXPECTED_RAW_FIELDS:
            posting[field] = f"value-of-{field}"

        projected = factual_postings({"test1": posting})["test1"]

        self.assertEqual(projected, posting)
        self.assertEqual(set(projected), EXPECTED_RAW_FIELDS)

    def test_unknown_keys_are_dropped(self):
        # The ticket originally claimed unknown keys survive; they do not:
        # factual_postings keeps only RAW_POSTING_FIELDS. Ticket wording was
        # corrected to match this behaviour.
        key = "karriere.at7818416"
        self.assertIn("unknown_field", self.postings[key])
        self.assertNotIn("unknown_field", self.factual[key])

    def test_projection_keeps_raw_values(self):
        key = "karriere.at7818416"
        expected = {
            field: value
            for field, value in self.postings[key].items()
            if field in EXPECTED_RAW_FIELDS
        }
        self.assertEqual(self.factual[key], expected)


class MergeObservationsTests(unittest.TestCase):
    def setUp(self):
        self.previous = load_fixture("merge_previous.json")
        self.current = load_fixture("merge_current.json")
        self.history = merge_observations(copy.deepcopy(self.current), copy.deepcopy(self.previous))

    def test_first_collected_on_is_the_earliest_known(self):
        self.assertEqual(self.history["karriere.at7818416"]["first_collected_on"], "2025-01-10")

    def test_last_collected_on_is_the_latest_known(self):
        self.assertEqual(self.history["karriere.at7818416"]["last_collected_on"], "2025-02-20")

    def test_timespan_days_is_recomputed(self):
        self.assertEqual(self.history["karriere.at7818416"]["timespan_days"], 41)

    def test_new_posting_becomes_its_own_range(self):
        posting = self.history["karriere.at7818418"]
        self.assertEqual(posting["first_collected_on"], "2025-02-20")
        self.assertEqual(posting["last_collected_on"], "2025-02-20")
        self.assertEqual(posting["timespan_days"], 0)

    def test_untouched_posting_is_preserved(self):
        self.assertEqual(self.history["karriere.at7820001"], self.previous["karriere.at7820001"])

    def test_latest_description_wins(self):
        self.assertEqual(
            self.history["karriere.at7818416"]["description"],
            "Build and operate the data platform.",
        )

    def test_empty_later_description_keeps_the_previous_one(self):
        # B27a: an empty observation does not erase a stored fact, so the
        # previous non-empty description survives.
        self.assertEqual(
            self.history["karriere.at7818419"]["description"],
            "Keep the reports running.",
        )

    def test_previous_scalar_survives_when_current_omits_it(self):
        self.assertEqual(self.history["karriere.at7818416"]["snippet"], "Python and SQL.")

    def test_matched_titlewords_is_an_ordered_union(self):
        self.assertEqual(
            self.history["karriere.at7818416"]["matched_titlewords"],
            ["data", "platform", "engineer"],
        )

    def test_history_matches_the_expected_fixture(self):
        self.assertEqual(self.history, load_fixture("merge_expected.json"))

    def test_second_merge_is_idempotent(self):
        current = copy.deepcopy(self.current)
        history = merge_observations(current, copy.deepcopy(self.previous))
        again = merge_observations(current, history)
        self.assertEqual(again, history)


class LastModifiedOnMergeTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_fixture("merge_last_modified_cases.json")

    def merge(self, case):
        current = copy.deepcopy(self.cases[case]["current"])
        previous = copy.deepcopy(self.cases[case]["previous"])
        return merge_observations(current, previous)

    def assert_expected(self, case, merged):
        for field, value in self.cases[case]["expected"].items():
            self.assertEqual(merged["test1"][field], value, field)

    def test_first_observation_last_modified_on_equals_collected_on(self):
        self.assert_expected("first_observation", self.merge("first_observation"))

    def test_unchanged_observation_keeps_last_modified_on_and_advances_last_collected_on(self):
        merged = self.merge("unchanged_observation")
        self.assert_expected("unchanged_observation", merged)

    def test_changed_description_moves_last_modified_on(self):
        self.assert_expected("changed_description", self.merge("changed_description"))

    def test_changed_title_moves_last_modified_on(self):
        self.assert_expected("changed_title", self.merge("changed_title"))

    def test_repeated_merge_does_not_move_last_modified_on(self):
        case = "unchanged_observation"
        history = self.merge(case)
        repeated = merge_observations(
            copy.deepcopy(self.cases[case]["current"]), history
        )
        self.assertEqual(history["test1"]["last_modified_on"], "2025-03-01")
        self.assertEqual(repeated["test1"]["last_modified_on"], "2025-03-01")
        self.assertEqual(repeated["test1"]["last_collected_on"], "2025-03-10")

    def test_legacy_record_without_field_keeps_last_known_change_date(self):
        merged = self.merge("legacy_record_unchanged")
        self.assert_expected("legacy_record_unchanged", merged)
        self.assertIsNotNone(merged["test1"]["last_modified_on"])

    def test_empty_observation_of_empty_record_is_not_a_change(self):
        self.assert_expected("empty_observation_of_empty_record",
                             self.merge("empty_observation_of_empty_record"))

    def test_empty_scalar_keeps_stored_value(self):
        self.assert_expected("empty_scalar_keeps_stored_value",
                             self.merge("empty_scalar_keeps_stored_value"))

    def test_empty_list_keeps_stored_value(self):
        self.assert_expected("empty_list_keeps_stored_value",
                             self.merge("empty_list_keeps_stored_value"))

    def test_false_replaces_stored_value(self):
        self.assert_expected("false_replaces_stored_value",
                             self.merge("false_replaces_stored_value"))

    def test_zero_replaces_stored_value(self):
        self.assert_expected("zero_replaces_stored_value",
                             self.merge("zero_replaces_stored_value"))

    def test_empty_derived_value_replaces(self):
        self.assert_expected("empty_derived_value_replaces",
                             self.merge("empty_derived_value_replaces"))

    def test_empty_title_does_not_move_last_modified_on(self):
        self.assert_expected("empty_title_does_not_move_last_modified_on",
                             self.merge("empty_title_does_not_move_last_modified_on"))

    def test_absent_title_does_not_move_last_modified_on(self):
        self.assert_expected("absent_title_does_not_move_last_modified_on",
                             self.merge("absent_title_does_not_move_last_modified_on"))

    def test_legacy_record_without_any_stored_date_uses_the_observation_date(self):
        # No stored date resolves, but the observation itself is dated, so the
        # field must still have a value.
        previous = {"test1": {"id": "1", "source": "test", "title": "Data Engineer",
                              "description": "Build the platform."}}
        current = {"test1": {"id": "1", "source": "test", "title": "Data Engineer",
                             "description": "Build the platform.",
                             "collected_on": "2025-03-10"}}

        merged = merge_observations(copy.deepcopy(current), copy.deepcopy(previous))

        self.assertEqual(merged["test1"]["last_modified_on"], "2025-03-10")

    def test_record_without_any_observation_date_omits_last_modified_on(self):
        # Nothing carries a date, so there is no honest value to record.
        current = {"test1": {"id": "1", "source": "test", "title": "Data Engineer"}}

        merged = merge_observations(copy.deepcopy(current), {})

        self.assertNotIn("last_modified_on", merged["test1"])

    def test_merge_owned_fields_are_never_taken_from_the_observation(self):
        current = {"test1": {"id": "1", "source": "test", "title": "Data Engineer",
                             "timespan_days": 5, "last_modified_on": "2025-02-01"}}

        merged = merge_observations(copy.deepcopy(current), {})

        self.assertNotIn("timespan_days", merged["test1"])
        self.assertNotIn("last_modified_on", merged["test1"])


class LastModifiedOnStorageTests(unittest.TestCase):
    def test_new_universal_record_carries_last_modified_on(self):
        raw = {"test1": {"id": "1", "source": "test", "title": "Data Engineer",
                         "description": "Build the platform.",
                         "collected_on": "2025-03-01"}}
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            stored = store_universal_postings(copy.deepcopy(raw), folder, {"scope": "test"})

        self.assertEqual(stored["test1"]["last_modified_on"], "2025-03-01")

    def test_scraper_raw_output_has_no_last_modified_on(self):
        scraper = KarriereAT(
            driver="", keywords={"titlewords": ["sales"], "locations": ["Vienna"]},
            date_day="2025-03-01",
        )
        responses = [[listing_response([listing()])], [detail_response("<p>Details</p>")]]
        with patch.object(http, "requests_responses_with_cookies", side_effect=responses):
            raw = scraper.gather_data(process=False, descriptions=True)

        self.assertTrue(raw)
        for posting in raw.values():
            self.assertNotIn("last_modified_on", posting)


class GetAddedAndRemovedTests(unittest.TestCase):
    def setUp(self):
        self.current = load_fixture("diff_current.json")
        self.previous = load_fixture("diff_previous.json")
        self.added, self.removed = get_added_and_removed(
            copy.deepcopy(self.current), copy.deepcopy(self.previous)
        )

    def test_added_identities(self):
        self.assertEqual(
            set(self.added),
            {"karriere.at7818418", "karriere.at7818419", "karriere.at7820000"},
        )

    def test_removed_identities(self):
        self.assertEqual(
            set(self.removed),
            {"karriere.at7818417", "karriere.at7820001"},
        )

    def test_unchanged_identity_is_neither_added_nor_removed(self):
        self.assertNotIn("karriere.at7818416", self.added)
        self.assertNotIn("karriere.at7818416", self.removed)

    def test_output_follows_input_insertion_order(self):
        self.assertEqual(list(self.added), [k for k in self.current if k not in self.previous])
        self.assertEqual(list(self.removed), [k for k in self.previous if k not in self.current])

    def test_equal_points_are_not_ordered(self):
        # Ties fall back to the iteration order of a set difference, which
        # changes between interpreter runs (observed with different hash
        # seeds), so only membership is asserted here.
        current = {f"karriere.at{number}": {"id": str(number)} for number in range(5)}
        added, _ = get_added_and_removed(current, {})

        self.assertEqual(set(added), set(current))


if __name__ == "__main__":
    unittest.main()
