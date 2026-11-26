"""Tests for the data-layer merge seam (B27)."""

import copy
import json
import unittest
from pathlib import Path

from jobscraping.data.merge import merge_observations, rebuild_history
from jobscraping.processing.attributes import merge_matched_titlewords
from jobscraping.processing.postings_utils import _has_value as has_value

FIXTURES = Path(__file__).with_name("fixtures")


def load_fixture(name):
    with open(FIXTURES / name, encoding="utf-8") as file:
        return json.load(file)


class RebuildHistoryTests(unittest.TestCase):
    def setUp(self):
        self.previous = load_fixture("merge_previous.json")
        self.current = load_fixture("merge_current.json")

    def rebuild(self):
        return rebuild_history(copy.deepcopy(self.current), copy.deepcopy(self.previous))

    def test_history_is_the_merged_observations(self):
        history, _ = self.rebuild()

        self.assertEqual(history, load_fixture("merge_expected.json"))

    def test_added_is_the_current_key_difference_in_insertion_order(self):
        history, added = self.rebuild()

        self.assertEqual(list(added), ["karriere.at7818418"])
        self.assertEqual(added["karriere.at7818418"], history["karriere.at7818418"])

    def test_current_records_carry_the_merged_values(self):
        current = copy.deepcopy(self.current)
        rebuild_history(current, copy.deepcopy(self.previous))

        self.assertEqual(current["karriere.at7818416"]["first_collected_on"], "2025-01-10")

    def test_repeated_rebuild_writes_byte_identical_history(self):
        first, _ = self.rebuild()
        second, _ = self.rebuild()

        self.assertEqual(json.dumps(first), json.dumps(second))

    def test_rebuild_of_its_own_history_is_idempotent(self):
        history, _ = self.rebuild()
        again, _ = rebuild_history(copy.deepcopy(self.current), copy.deepcopy(history))

        self.assertEqual(again, history)
        self.assertEqual(merge_observations(copy.deepcopy(self.current), history), history)


class SharedRuleDefinitionTests(unittest.TestCase):
    def test_postings_utils_has_value_matches_the_merge_rule_behaviour(self):
        from jobscraping.data import merge

        values = [None, "", [], {}, False, 0, "x"]

        self.assertEqual([has_value(value) for value in values],
                         [merge.has_value(value) for value in values])

    def test_postings_utils_cache_fields_derive_from_the_merge_group(self):
        from jobscraping.data import merge
        from jobscraping.processing import postings_utils

        self.assertEqual(postings_utils.CACHE_ALWAYS_FRESH_FIELDS,
                         set(merge.ALWAYS_FRESH_FIELDS))


class MatchedTitlewordsReexportTests(unittest.TestCase):
    def test_processing_attributes_keeps_the_public_name(self):
        target = {"matched_titlewords": ["data"]}

        merge_matched_titlewords(target, {"matched_titlewords": ["platform", "data"]})

        self.assertEqual(target["matched_titlewords"], ["data", "platform"])


if __name__ == "__main__":
    unittest.main()
