import unittest

from jobscraping.acquisition.quality import validate_postings_quality


class QualityGateTests(unittest.TestCase):
    def test_required_field_present_passes(self):
        postings = {
            "1": {"source": "karriere.at", "description": "text"},
            "2": {"source": "karriere.at", "description": "text"},
        }

        validate_postings_quality(
            postings,
            required_fields_by_source={"karriere.at": ("description",)},
        )

    def test_missing_required_field_fails(self):
        postings = {
            "1": {"source": "karriere.at", "description": "text"},
            "2": {"source": "karriere.at", "description": ""},
        }

        with self.assertRaisesRegex(ValueError, r"karriere\.at: description=1"):
            validate_postings_quality(
                postings,
                required_fields_by_source={"karriere.at": ("description",)},
            )

    def test_source_retention_above_threshold_passes(self):
        previous = {
            f"old{index}": {"source": "karriere.at"} for index in range(4)
        }
        current = {
            f"new{index}": {"source": "karriere.at"} for index in range(3)
        }

        validate_postings_quality(
            current,
            previous_postings=previous,
            minimum_source_retention={"karriere.at": 0.5},
        )

    def test_source_retention_below_threshold_fails(self):
        previous = {
            f"old{index}": {"source": "karriere.at"} for index in range(10)
        }
        current = {
            f"new{index}": {"source": "karriere.at"} for index in range(4)
        }

        with self.assertRaisesRegex(ValueError, "retained 4/10"):
            validate_postings_quality(
                current,
                previous_postings=previous,
                minimum_source_retention={"karriere.at": 0.5},
            )


if __name__ == "__main__":
    unittest.main()
