"""Contract tests for the data specs (B08)."""

import copy
import unittest

from jobscraping.specs.base import DataSpec, FieldSpec
from jobscraping.specs.postings import (
    COLLECTED_POSTINGS,
    DISCOVERED_POSTINGS,
    SCORED_POSTINGS,
    SELECTED_POSTINGS,
    UNIVERSAL_POSTINGS,
)

RECORD = {"source": "karriere.at", "id": "1", "url": "https://example.test/1"}


class DataSpecTest(unittest.TestCase):
    def test_missing_required_field_is_reported_by_name(self):
        records = {"karriere.at1": {"source": "karriere.at", "id": "1"}}
        self.assertEqual(
            DISCOVERED_POSTINGS.check(records),
            ["karriere.at1: missing required field 'url'"],
        )

    def test_unknown_fields_pass_and_are_not_removed(self):
        records = {"karriere.at1": {**RECORD, "brand_new_key": [1, 2]}}
        self.assertEqual(DISCOVERED_POSTINGS.check(records), [])
        self.assertEqual(records["karriere.at1"]["brand_new_key"], [1, 2])

    def test_extend_returns_a_new_spec(self):
        extra = FieldSpec("salary_expectation", "float")
        extended = SCORED_POSTINGS.extend(extra)
        self.assertIsInstance(extended, DataSpec)
        self.assertEqual(extended.name, SCORED_POSTINGS.name)
        self.assertEqual(extended.key, SCORED_POSTINGS.key)
        self.assertEqual(extended.fields[-1], extra)
        self.assertEqual(extended.fields[:-1], SCORED_POSTINGS.fields)
        self.assertNotIn(extra, SCORED_POSTINGS.fields)

    def test_check_does_not_mutate_or_coerce_records(self):
        records = {"karriere.at1": {"source": "karriere.at", "id": "1", "url": 7}}
        before = copy.deepcopy(records)
        self.assertEqual(DISCOVERED_POSTINGS.check(records), [])
        self.assertEqual(records, before)

    def test_optional_fields_may_be_absent(self):
        self.assertEqual(DISCOVERED_POSTINGS.check({"karriere.at1": dict(RECORD)}), [])

    def test_every_missing_required_field_is_reported(self):
        problems = SCORED_POSTINGS.check({"karriere.at1": {"source": "karriere.at"}})
        self.assertEqual(
            problems,
            [
                "karriere.at1: missing required field 'id'",
                "karriere.at1: missing required field 'points'",
            ],
        )

    def test_posting_specs_share_the_identity_key(self):
        for spec in (DISCOVERED_POSTINGS, COLLECTED_POSTINGS, UNIVERSAL_POSTINGS,
                     SCORED_POSTINGS, SELECTED_POSTINGS):
            self.assertEqual(spec.key, ("source", "id"))


ANNOTATIONS = ("language", "matched_titlewords", "guessed_required_languages")
POLICY_FIELDS = (
    "points",
    "keywords",
    "role_families",
    "language_adjustment",
    "language_excluded",
    "profile_excluded",
)
CARRIED_SPECS = (UNIVERSAL_POSTINGS, SCORED_POSTINGS, SELECTED_POSTINGS)


class ProfileNeutralAnnotationTest(unittest.TestCase):
    """Q29: annotations describe the posting; policy fields describe a profile."""

    def test_universal_declares_the_annotations(self):
        names = {field.name for field in UNIVERSAL_POSTINGS.fields}
        self.assertLessEqual(set(ANNOTATIONS), names)

    def test_universal_declares_no_policy_field(self):
        names = {field.name for field in UNIVERSAL_POSTINGS.fields}
        self.assertEqual(set(POLICY_FIELDS) & names, set())

    def test_annotations_are_carried_from_enrichment(self):
        universal = {field.name: field.produced_by for field in UNIVERSAL_POSTINGS.fields}
        for spec in (SCORED_POSTINGS, SELECTED_POSTINGS):
            producers = {field.name: field.produced_by for field in spec.fields}
            for name in ANNOTATIONS:
                self.assertEqual(producers[name], universal[name], f"{spec.name}.{name}")

    def test_language_annotations_come_from_enrichment(self):
        for spec in CARRIED_SPECS:
            producers = {field.name: field.produced_by for field in spec.fields}
            for name in ("language", "guessed_required_languages"):
                self.assertEqual(producers[name], "enrichment", f"{spec.name}.{name}")

    def test_policy_fields_are_derived(self):
        producers = {field.name: field.produced_by for field in SCORED_POSTINGS.fields}
        for name in POLICY_FIELDS:
            self.assertEqual(producers[name], "derivation", f"scored_postings.{name}")

    def test_guessed_required_languages_is_a_dict(self):
        for spec in CARRIED_SPECS:
            kinds = {field.name: field.kind for field in spec.fields}
            self.assertEqual(kinds["guessed_required_languages"], "dict", spec.name)


if __name__ == "__main__":
    unittest.main()
