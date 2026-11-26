"""Tests for the neutral identity diff (B28)."""

import copy
import unittest

from jobscraping.data.compare import get_added_and_removed


class NeutralDiffTests(unittest.TestCase):
    def setUp(self):
        self.current = {
            "karriere.at1": {"id": "1", "title": "Data Engineer"},
            "karriere.at2": {"id": "2", "title": "Analyst"},
        }
        self.previous = {
            "karriere.at2": {"id": "2", "title": "Analyst"},
            "karriere.at3": {"id": "3", "title": "BI Developer"},
        }

    def diff(self, new, previous):
        return get_added_and_removed(copy.deepcopy(new), copy.deepcopy(previous))

    def test_added_is_the_new_key_difference(self):
        added, _ = self.diff(self.current, self.previous)

        self.assertEqual(list(added), ["karriere.at1"])
        self.assertEqual(added["karriere.at1"], self.current["karriere.at1"])

    def test_removed_is_the_previous_key_difference(self):
        _, removed = self.diff(self.current, self.previous)

        self.assertEqual(list(removed), ["karriere.at3"])
        self.assertEqual(removed["karriere.at3"], self.previous["karriere.at3"])

    def test_unchanged_identity_is_neither_added_nor_removed(self):
        added, removed = self.diff(self.current, self.previous)

        self.assertNotIn("karriere.at2", added)
        self.assertNotIn("karriere.at2", removed)

    def test_order_follows_input_insertion_order(self):
        current = {f"karriere.at{number}": {"id": str(number)} for number in (5, 3, 9)}
        previous = {f"karriere.at{number}": {"id": str(number)} for number in (8, 4)}

        added, removed = self.diff(current, previous)

        self.assertEqual(list(added), ["karriere.at5", "karriere.at3", "karriere.at9"])
        self.assertEqual(list(removed), ["karriere.at8", "karriere.at4"])

    def test_reappearing_identity_is_only_newly_added_against_the_previous_current(self):
        history = {
            "karriere.at1": {"id": "1", "first_collected_on": "2025-01-01"},
            "karriere.at2": {"id": "2", "first_collected_on": "2025-01-02"},
        }
        previous_current = {"karriere.at2": {"id": "2"}}
        current = {"karriere.at1": {"id": "1"}, "karriere.at2": {"id": "2"}}

        added_against_history, _ = self.diff(current, history)
        added_against_previous_current, _ = self.diff(current, previous_current)

        self.assertEqual(added_against_history, {})
        self.assertEqual(list(added_against_previous_current), ["karriere.at1"])

    def test_records_keep_no_injected_points_key(self):
        added, removed = self.diff(self.current, self.previous)

        for record in (*added.values(), *removed.values()):
            self.assertNotIn("points", record)

    def test_inputs_are_not_mutated(self):
        current = copy.deepcopy(self.current)
        previous = copy.deepcopy(self.previous)

        get_added_and_removed(current, previous)

        self.assertEqual(current, self.current)
        self.assertEqual(previous, self.previous)


if __name__ == "__main__":
    unittest.main()
