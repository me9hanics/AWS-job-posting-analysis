import tempfile
import unittest
import json
from copy import deepcopy
from pathlib import Path

from jobscraping.processing.derive_profile_postings import derive_profile_postings
from jobscraping.profiles.dani import DANI_INTERESTS, DANI_LANGUAGE_POLICY
from jobscraping.scrapers.steps import Step
from schedule.dani_collect import get_dani_postings
from unittest.mock import patch


def posting(title="Account Manager", description="We work with our customers and you will help us grow.", **fields):
    return {"title": title, "company": "Company", "description": description,
            "source": "karriere.at", "locations": ["Vienna"],
            "collected_on": "2026-11-03", **fields}


class DaniProfileTests(unittest.TestCase):
    def test_cached_scores_are_recomputed_and_known_reappearances_are_not_new(self):
        previous = {
            "known": posting(points=-9, first_collected_on="2026-10-01"),
            "absent": posting(points=2),
        }
        raw = {"known": posting(points=99), "new": posting(description="Native German required")}
        original = deepcopy(raw)
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            data = derive_profile_postings(raw, path=folder, previous_history=previous)
        self.assertEqual(set(data["results"]), {"known"})
        self.assertEqual(data["added"], {})
        self.assertEqual(set(data["removed"]), {"absent"})
        self.assertAlmostEqual(data["results"]["known"]["points"], 2.36)
        self.assertEqual(data["results"]["known"]["first_collected_on"], "2026-10-01")
        self.assertEqual(raw, original)

    def test_new_role_aliases_do_not_accumulate_within_family(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            data = derive_profile_postings({
                "one": posting(title="Business Analyst", description=""),
                "aliases": posting(title="Business Analyst / IT Business Analyst / Process Improvement Specialist", description=""),
            }, path=folder, previous_history={})
        self.assertEqual(data["results"]["one"]["points"], .45)
        self.assertEqual(data["results"]["aliases"]["points"], .45)

    def test_existing_sales_operations_manager_keeps_its_role_contribution(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            data = derive_profile_postings({"id": posting(title="Sales Operations Manager", description="")},
                path=folder, previous_history={})
            self.assertEqual(data["results"]["id"]["points"], 1.0)

    def test_non_vienna_locations_receive_an_extra_deduction(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            data = derive_profile_postings({
                "vienna": posting(title="Enterprise Account Executive", description="",
                                  salary_monthly_guessed=3300),
                "linz": posting(title="Enterprise Account Executive", description="",
                                locations=["Linz"], salary_monthly_guessed=3300),
                "wiener_neudorf": posting(title="Enterprise Account Executive", description="",
                                            locations=["Wiener Neudorf"], salary_monthly_guessed=3300),
            }, path=folder, previous_history={})
        self.assertAlmostEqual(
            data["results"]["vienna"]["points"] - data["results"]["linz"]["points"],
            1.75,
        )
        self.assertAlmostEqual(
            data["results"]["vienna"]["points"] - data["results"]["wiener_neudorf"]["points"],
            0.75,
        )

    def test_priority_commercial_finance_titles_outrank_broader_interests(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            data = derive_profile_postings({
                "priority": posting(title="Enterprise Account Executive", description=""),
                "broader": posting(title="Financial Analyst", description=""),
            }, path=folder, previous_history={})
        self.assertIn("broader", data["results"])
        self.assertGreaterEqual(
            data["results"]["priority"]["points"] - data["results"]["broader"]["points"],
            1.5,
        )

    def test_every_confirmed_priority_title_gets_the_priority_family(self):
        titles = (
            "Business Development Manager — Fintech", "Partnerships Manager — Financial Services",
            "Corporate Sales Manager", "Merchant Acquisition Manager", "Payment Solutions Sales Manager",
            "Corporate Banking Relationship Manager", "Client Relationship Manager — Financial Services",
            "Enterprise Account Executive", "Strategic Account Manager", "Key Account Manager — B2B",
            "Business Development Manager", "Strategic Partnerships Manager", "Commercial Development Manager",
            "International Sales Manager", "Institutional Sales Associate", "Investment Solutions Sales",
            "Corporate Finance Business Development", "Debt Financing / Lending Sales",
            "Investor Relations Associate", "M&A Origination Associate",
        )
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            data = derive_profile_postings({title: posting(title=title, description="") for title in titles},
                                           path=folder, previous_history={})
        for title in titles:
            self.assertIn("priority_commercial_finance", data["results"][title]["role_families"])

    def test_candidate_history_retains_exclusions_and_replaces_derived_values(self):
        raw = {"id": posting(description="We need fluent German for our customers.")}
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            old = {"id": posting(points=99, keywords=["stale"], first_collected_on="2026-09-01")}
            first = derive_profile_postings(raw, path=folder, previous_history=old)
            self.assertEqual(first["results"], {})
            policy = {**DANI_LANGUAGE_POLICY, "fluent": -.5}
            second = derive_profile_postings(raw, path=folder, language_policy=policy)
            third = derive_profile_postings(raw, path=folder, language_policy=policy)
            self.assertEqual(second["added"], {})
            self.assertEqual(second["results"], third["results"])
            self.assertGreater(second["results"]["id"]["points"], 0)
            stored = json.loads((Path(folder) / "postings_history.json").read_text())
            self.assertEqual(stored["id"]["first_collected_on"], "2026-09-01")
            self.assertNotIn("stale", stored["id"]["keywords"])
            self.assertEqual(stored["id"]["points"], second["results"]["id"]["points"])
            baseline = list(Path(folder).glob("migration_baseline_*.json"))
            self.assertEqual(len(baseline), 1)
            self.assertEqual(json.loads(baseline[0].read_text())["id"]["points"], 99)

    def test_native_low_scores_and_title_exclusions_stay_in_candidate_artifacts(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            data = derive_profile_postings({
                "native": posting(description="Native German required"),
                "low": posting(title="Business Analyst", description="German C1 required"),
                "director": posting(title="Sales Director"),
            }, path=folder, previous_history={})
            self.assertEqual(data["results"], {})
            for name in ("current_postings.json", "postings_history.json", "newly_added_postings.json"):
                self.assertEqual(set(json.loads((Path(folder) / name).read_text())), {"native", "low", "director"})

    def test_all_63_interests_are_candidates_and_substrings_do_not_exclude(self):
        interests = [label for labels in DANI_INTERESTS.values() for label in labels]
        self.assertEqual(len(set(interests)), 63)
        raw = {label: posting(title=label, description="") for label in interests}
        raw.update({"international": posting(title="International Project Coordinator"),
                    "lead": posting(title="Lead Generation Specialist"),
                    "projekt": posting(title="Projektleiter"),
                    "irrelevant": posting(title="Cook", description="Kitchen")})
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            data = derive_profile_postings(raw, path=folder, previous_history={})
            self.assertEqual(set(data["results"]), set(raw) - {"irrelevant"})
            stored = json.loads((Path(folder) / "current_postings.json").read_text())
            self.assertNotIn("irrelevant", stored)

    def test_empty_success_preserves_history_based_removed_delta(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            data = derive_profile_postings({}, path=folder, previous_history={"old": posting(points=2)})
            self.assertEqual(data["results"], {})
            self.assertEqual(data["companies"], [])
            self.assertIsNone(data["excel_file_path"])
            self.assertEqual(set(data["removed"]), {"old"})
            self.assertEqual(json.loads((Path(folder) / "current_postings.json").read_text()), {})

    def test_severe_non_native_requirements_can_survive_and_optional_native_is_eligible(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            data = derive_profile_postings({
                "strong": posting(title="Key Account Manager / Technical Sales",
                    description="We need fluent German. Salesforce CRM ERP Excel Power BI", salary_monthly_guessed=3300),
                "optional": posting(description="Native German optional"),
            }, path=folder, previous_history={})
            self.assertEqual(set(data["results"]), {"strong", "optional"})
            self.assertEqual(data["results"]["strong"]["language_adjustment"], -4)

    def test_removed_legacy_candidates_obey_native_eligibility_without_resetting_delta_threshold(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            data = derive_profile_postings({}, path=folder, previous_history={
                "native": posting(description="Native German required", points=9),
                "known": posting(description="German C1 required", points=2),
            })
            self.assertEqual(set(data["removed"]), {"known"})

    def test_added_and_removed_are_ordered_by_points_after_derivation(self):
        previous = {
            "low": posting(points=1, first_collected_on="2026-10-01"),
            "high": posting(points=50, first_collected_on="2026-10-01"),
            "legacy": posting(first_collected_on="2026-10-01"),
        }
        raw = {"a": posting(title="Data Engineer"), "b": posting(title="Account Manager")}
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            data = derive_profile_postings(raw, path=folder, previous_history=previous, threshold=None)

        self.assertEqual(list(data["removed"]), ["high", "low", "legacy"])
        for kind in ("added", "removed"):
            points = [p["points"] for p in data[kind].values()]
            self.assertEqual(points, sorted(points, reverse=True))

    def test_previous_file_fallback_keeps_known_ids_out_of_new_feed(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            (Path(folder) / "postings_2026-10-01.json").write_text(json.dumps({"known": posting(points=-5)}))
            data = derive_profile_postings({"known": posting()}, path=folder)
            self.assertIn("known", data["results"])
            self.assertEqual(data["added"], {})

    def test_entrypoint_quality_gate_uses_raw_counts_before_strict_selection(self):
        class Source:
            source = "test"
            postings = {"native": posting(description="Native German required")}

            def __init__(self, **kwargs):
                self.steps = (Step("all", self.collect),)

            def collect(self, records, config):
                return deepcopy(self.postings)

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            path = Path(folder)
            profile = path / "dani"
            raw = path / "universal" / "collections" / "dani"
            broad = path / "universal" / "postings_history.json"
            broad.parent.mkdir()
            broad.write_text('{"broader": {}}')
            with patch("schedule.dani_collect.generate_outputs") as excel:
                first = get_dani_postings(path=str(profile), raw_path=str(raw), scrapers=[Source], path_excel=None)
                second = get_dani_postings(path=str(profile), raw_path=str(raw), scrapers=[Source], path_excel=None)
                self.assertEqual(first["results"], {})
                self.assertEqual(second["results"], {})
                self.assertEqual(set(first), {"results", "added", "removed", "companies", "excel_file_path"})
                excel.assert_not_called()
            self.assertIn("native", json.loads((raw / "current_postings.json").read_text()))
            self.assertEqual(broad.read_text(), '{"broader": {}}')
            healthy_profile = (profile / "current_postings.json").read_bytes()
            healthy_raw = (raw / "current_postings.json").read_bytes()
            Source.postings = {"incomplete": posting(description="")}
            with self.assertRaisesRegex(ValueError, "quality gate"):
                get_dani_postings(path=str(profile), raw_path=str(raw), scrapers=[Source], path_excel=None)
            self.assertEqual((profile / "current_postings.json").read_bytes(), healthy_profile)
            self.assertEqual((raw / "current_postings.json").read_bytes(), healthy_raw)
            Source.postings = {}
            with self.assertRaisesRegex(RuntimeError, "no records"):
                get_dani_postings(path=str(profile), raw_path=str(raw), scrapers=[Source], path_excel=None)
            self.assertEqual((profile / "current_postings.json").read_bytes(), healthy_profile)
            self.assertEqual((raw / "current_postings.json").read_bytes(), healthy_raw)
            with self.assertRaisesRegex(RuntimeError, "no records"):
                get_dani_postings(path=str(profile), raw_path=str(raw), scrapers=[Source],
                    minimum_source_retention={}, path_excel=None)
            self.assertEqual((profile / "current_postings.json").read_bytes(), healthy_profile)
            self.assertEqual((raw / "current_postings.json").read_bytes(), healthy_raw)
