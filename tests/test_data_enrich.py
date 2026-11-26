"""Tests for the data-layer enrichment seam (B29)."""

import json
import unittest

from jobscraping.data.enrich import (
    annotate_postings,
    enrich_postings,
    get_date_of_collection,
)

ENGLISH_DESCRIPTION = "We are looking for a developer. Fluent German required."
GERMAN_DESCRIPTION = "Wir suchen einen Entwickler für die Abteilung. Fließende Deutschkenntnisse erforderlich."


class AnnotatePostingsTests(unittest.TestCase):
    def test_record_with_description_gains_both_annotations(self):
        postings = {"1": {"title": "Developer", "description": ENGLISH_DESCRIPTION}}

        annotated = annotate_postings(postings)

        self.assertEqual(annotated["1"]["language"], "en")
        self.assertEqual(annotated["1"]["guessed_required_languages"], {"German": "fluent"})

    def test_german_description_is_detected(self):
        annotated = annotate_postings({"1": {"title": "Entwickler", "description": GERMAN_DESCRIPTION}})

        self.assertEqual(annotated["1"]["language"], "de")
        self.assertEqual(annotated["1"]["guessed_required_languages"], {"German": "fluent"})

    def test_record_without_description_is_untouched(self):
        postings = {"1": {"title": "Developer", "company": "ACME"}}

        annotate_postings(postings)

        self.assertEqual(postings["1"], {"title": "Developer", "company": "ACME"})

    def test_empty_description_is_untouched(self):
        postings = {"1": {"title": "Developer", "description": ""}}

        annotate_postings(postings)

        self.assertNotIn("language", postings["1"])
        self.assertNotIn("guessed_required_languages", postings["1"])

    def test_rerun_replaces_values_and_stays_byte_identical(self):
        postings = {"1": {"title": "Developer", "description": ENGLISH_DESCRIPTION,
                          "language": "de", "guessed_required_languages": {"Old": "C2"}}}

        once = annotate_postings(postings)
        first_dump = json.dumps(once, sort_keys=True)
        twice = annotate_postings(once)

        self.assertEqual(json.dumps(twice, sort_keys=True), first_dump)
        self.assertEqual(twice["1"]["language"], "en")
        self.assertEqual(twice["1"]["guessed_required_languages"], {"German": "fluent"})

    def test_custom_description_key_is_used(self):
        postings = {"1": {"title": "Developer", "body": ENGLISH_DESCRIPTION}}

        annotate_postings(postings, description_key="body")

        self.assertEqual(postings["1"]["language"], "en")
        self.assertEqual(postings["1"]["guessed_required_languages"], {"German": "fluent"})


class GetDateOfCollectionTests(unittest.TestCase):
    def test_existing_value_wins_unless_overwritten(self):
        posting = {"collected_on": "2025-01-02"}

        self.assertEqual(get_date_of_collection(value=posting), "2025-01-02")
        self.assertEqual(
            get_date_of_collection(value=posting, filename="run_2025-03-04.json", overwrite=True),
            "2025-03-04",
        )

    def test_date_is_read_from_the_filename(self):
        self.assertEqual(get_date_of_collection(filename="postings_2025-03-04.json"), "2025-03-04")

    def test_undated_filename_yields_nothing(self):
        self.assertIsNone(get_date_of_collection(filename="postings.json"))


class EnrichPostingsTests(unittest.TestCase):
    def test_salary_is_guessed_from_the_salary_field(self):
        postings = {"1": {"title": "Developer", "salary": "65.000 jährlich"}}

        enriched = enrich_postings(postings, filename="postings_2025-03-04.json")

        self.assertEqual(enriched["1"]["salary_guessed"], {"annual": 65000, "monthly": 5416})
        self.assertEqual(enriched["1"]["salary_monthly_guessed"], 5416)
        self.assertEqual(enriched["1"]["collected_on"], "2025-03-04")

    def test_salary_is_guessed_from_the_description(self):
        postings = {"1": {"title": "Developer", "description": "Gehalt: 60.000"}}

        enriched = enrich_postings(postings)

        self.assertEqual(enriched["1"]["salary_guessed"], {"annual": 60000, "monthly": 5000})
        self.assertEqual(enriched["1"]["salary_monthly_guessed"], 5000)

    def test_annotations_are_applied(self):
        postings = {"1": {"title": "Developer", "description": ENGLISH_DESCRIPTION}}

        enrich_postings(postings)

        self.assertEqual(postings["1"]["language"], "en")
        self.assertEqual(postings["1"]["guessed_required_languages"], {"German": "fluent"})

    def test_double_enrichment_is_byte_stable(self):
        postings = {"1": {"title": "Developer", "description": ENGLISH_DESCRIPTION,
                          "salary": "65.000 jährlich"}}

        once = enrich_postings(postings, filename="postings_2025-03-04.json")
        first = json.dumps(once, sort_keys=True)
        twice = enrich_postings(once, filename="postings_2025-03-04.json")

        self.assertEqual(json.dumps(twice, sort_keys=True), first)

    def test_existing_guesses_are_kept_without_overwrite(self):
        postings = {"1": {"title": "Developer", "salary": "65.000 jährlich",
                          "salary_guessed": {"annual": 1}, "salary_monthly_guessed": 1,
                          "collected_on": "2020-01-01"}}

        enrich_postings(postings, overwrite=False, filename="postings_2025-03-04.json")

        self.assertEqual(postings["1"]["salary_guessed"], {"annual": 1})
        self.assertEqual(postings["1"]["salary_monthly_guessed"], 1)
        self.assertEqual(postings["1"]["collected_on"], "2020-01-01")


if __name__ == "__main__":
    unittest.main()
