import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bs4 import BeautifulSoup

from jobscraping.data.merge import merge_observations
from jobscraping.pipelines.collecting import scrape_sites
from jobscraping.pipelines.scrape_universal import run_universal_scrape_flow
from jobscraping.profiles.dani import is_candidate
from jobscraping.scrapers import KarriereAT, Raiffeisen, http
from jobscraping.scrapers.steps import Step
from jobscraping.specs.postings import UNIVERSAL_POSTINGS


def listing(posting_id=1, title="Director Sales"):
    return {"jobsItem": {
        "id": posting_id, "title": title, "company": {"name": "Company"},
        "locations": [{"name": "Vienna"}], "salary": "", "isActive": True,
        "isHomeOffice": False, "employmentTypes": [],
        "link": f"https://www.karriere.at/jobs/{posting_id}", "snippet": "",
        "date": "2026-11-03",
    }}


def response(items=None, detail=None):
    from types import SimpleNamespace
    payload = ({"data": {"jobsSearchList": {"activeItems": {"items": items}}}}
               if items is not None else
               {"data": {"jobDetailContent": {"jobContent": {"text": detail}, "jobHeader": {"job": {"id": 1}}}}})
    return SimpleNamespace(text=json.dumps(payload))


def http_response(items=None, detail=None, status_code=200):
    result = response(items=items, detail=detail)
    result.status_code = status_code
    result.cookies = []
    return result


class RawCollectionTests(unittest.TestCase):
    def test_raw_quality_allows_configured_description_incompleteness(self):
        class Source:
            source = "test"

            def __init__(self, **kwargs):
                self.steps = (Step("all", self.collect),)

            def collect(self, records, config):
                postings = {}
                for index in range(50):
                    posting = {
                        "title": "Sales", "company": "Company", "source": "test",
                    }
                    if index:
                        posting["description"] = "Details"
                    postings[str(index)] = posting
                return postings

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            raw = run_universal_scrape_flow(
                path=folder,
                scrapers=[Source],
                minimum_field_completeness_by_source={"test": {"description": .98}},
            )

        self.assertIn("0", raw)
        self.assertNotIn("description", raw["0"])

    def test_raw_quality_rejects_description_below_configured_completeness(self):
        class Source:
            source = "test"

            def __init__(self, **kwargs):
                self.steps = (Step("all", self.collect),)

            def collect(self, records, config):
                postings = {}
                for index in range(50):
                    posting = {
                        "title": "Sales", "company": "Company", "source": "test",
                    }
                    if index >= 2:
                        posting["description"] = "Details"
                    postings[str(index)] = posting
                return postings

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            with self.assertRaisesRegex(ValueError, "description=2"):
                run_universal_scrape_flow(
                    path=folder,
                    scrapers=[Source],
                    minimum_field_completeness_by_source={"test": {"description": .98}},
                )

    def test_raw_karriere_treats_later_410_as_terminal_pagination(self):
        responses = [
            http_response([listing()]),
            http_response(status_code=410),
            http_response(detail="<p>Native German required</p>"),
        ]

        class Session:
            cookies = SimpleNamespace(set=lambda *_args: None)

            def get(self, *_args, **_kwargs):
                return responses.pop(0)

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            with (
                patch.object(http.requests, "Session", Session),
                patch.object(http.time, "sleep"),
            ):
                postings = run_universal_scrape_flow(
                    path=folder,
                    scrapers=[KarriereAT],
                    keywords={"titlewords": ["sales"], "locations": ["Vienna"]},
                )

        self.assertEqual(postings["karriere.at1"]["description"], "Native German required")

    def test_raw_karriere_first_page_410_preserves_healthy_artifacts(self):
        class Session:
            cookies = SimpleNamespace(set=lambda *_args: None)

            def get(self, *_args, **_kwargs):
                return http_response(status_code=410)

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            current = Path(folder) / "current_postings.json"
            healthy = '{"healthy": {"source": "karriere.at"}}'
            current.write_text(healthy)
            with (
                patch.object(http.requests, "Session", Session),
                patch.object(http.time, "sleep"),
                self.assertRaisesRegex(RuntimeError, "HTTP 410"),
            ):
                run_universal_scrape_flow(
                    path=folder,
                    scrapers=[KarriereAT],
                    keywords={"titlewords": ["sales"], "locations": ["Vienna"]},
                )

            self.assertEqual(current.read_text(), healthy)

    def test_legacy_karriere_410_behavior_is_unchanged(self):
        responses = [http_response([listing()]), http_response(status_code=410)]

        class Session:
            cookies = SimpleNamespace(set=lambda *_args: None)

            def get(self, *_args, **_kwargs):
                return responses.pop(0)

        scraper = KarriereAT(
            driver="", keywords={"titlewords": ["sales"], "locations": ["Vienna"]}
        )
        with (
            patch.object(http.requests, "Session", Session),
            patch.object(http.time, "sleep"),
        ):
            postings = scraper.gather_data(descriptions=False)

        self.assertIn("karriere.at1", postings)

    def test_raw_mode_keeps_rejected_title_and_reuses_only_facts(self):
        keywords = {"titlewords": ["sales"], "locations": ["Vienna"], "banned_words": ["director"]}
        cached = {"karriere.at1": {"title": "Director Sales", "company": "Company",
                  "description": "Native German required", "points": 99,
                  "keywords": ["obsolete"], "language_excluded": False}}
        with patch.object(http, "requests_responses_with_cookies", return_value=[response([listing()])]) as mocked_requests:
            # The scraper still discovers current activity; cache only skips details.
            raw = scrape_sites(scrapers=[KarriereAT], keywords=keywords, process=False,
                               cached_postings=cached, cache_mode="id-only", date_day="2026-11-03")
        self.assertEqual(raw["karriere.at1"]["description"], "Native German required")
        self.assertEqual(raw["karriere.at1"]["collected_on"], "2026-11-03")
        self.assertEqual(raw["karriere.at1"]["matched_titlewords"], ["sales"])
        self.assertNotIn("points", raw["karriere.at1"])
        self.assertNotIn("language_excluded", raw["karriere.at1"])
        self.assertEqual(mocked_requests.call_count, 1)

    def test_incomplete_raw_run_preserves_healthy_files_and_retains_evidence(self):
        class Source:
            source = "test"

            def __init__(self, **kwargs):
                self.steps = (Step("all", self.collect),)

            def collect(self, records, config):
                return {"id": {"title": "Director", "company": "Company", "source": "test"}}

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            path = Path(folder)
            healthy = '{"healthy": {"source": "test"}}'
            (path / "current_postings.json").write_text(healthy)
            with self.assertRaisesRegex(ValueError, "quality gate"):
                run_universal_scrape_flow(path=folder, scrapers=[Source],
                    required_fields_by_source={"test": ("description",)})
            self.assertEqual((path / "current_postings.json").read_text(), healthy)
            incomplete = list(path.glob("incomplete_run_*.json"))
            self.assertEqual(len(incomplete), 1)
            self.assertIn("id", json.loads(incomplete[0].read_text())["postings"])

    def test_raw_karriere_keeps_missing_details_and_fresh_equals_cache(self):
        keywords = {"titlewords": ["sales"], "locations": ["Vienna"], "banned_words": ["director"]}
        scraper = KarriereAT(driver="", keywords=keywords, date_day="2026-11-03")
        with patch.object(http, "requests_responses_with_cookies", side_effect=[
            [response([listing()])], [response(detail="<p>Native German required</p>")],
        ]):
            fresh = scraper.gather_data(process=False, descriptions=True)
        with patch.object(http, "requests_responses_with_cookies", return_value=[response([listing()])]):
            cached = scraper.gather_data(process=False, descriptions=True, cached_postings=fresh, cache_mode="id-only")
        self.assertEqual(fresh, cached)
        with patch.object(http, "requests_responses_with_cookies", side_effect=[
            [response([listing()])], [response(detail="<p>Refreshed details</p>")],
        ]) as mocked_requests:
            refreshed = scraper.gather_data(process=False, descriptions=True, cached_postings=fresh, cache_mode=None)
        self.assertEqual(refreshed["karriere.at1"]["description"], "Refreshed details")
        self.assertEqual(mocked_requests.call_count, 2)
        with patch.object(http, "requests_responses_with_cookies", side_effect=[[response([listing()])], []]):
            incomplete = scraper.gather_data(process=False, descriptions=True)
        self.assertIn("karriere.at1", incomplete)
        self.assertNotIn("description", incomplete["karriere.at1"])

    def test_raiffeisen_raw_mode_retains_titles_queries_and_missing_details(self):
        keywords = {"titlewords": ["sales"], "locations": [], "banned_words": ["director"]}
        scraper = Raiffeisen(driver="", keywords=keywords, date_day="2026-11-03")
        soup = BeautifulSoup('<a class="jobTitle-link" href="/job/director/1/">Director Sales</a>', "html.parser")
        detail = BeautifulSoup('<div class="joblayouttoken rtltextaligneligible displayDTM"><ul><li>Work</li></ul><ul><li>Native German required</li></ul><ul><li>Benefits</li></ul></div>', "html.parser")
        with patch.object(http, "requests_responses", side_effect=[[soup], [detail]]):
            raw = scraper.gather_data(process=False, descriptions=True)
        self.assertEqual(raw["raiffeisen_international1"]["matched_titlewords"], ["sales"])
        self.assertIn("Native German required", raw["raiffeisen_international1"]["description"])
        self.assertNotIn("points", raw["raiffeisen_international1"])
        with patch.object(http, "requests_responses", side_effect=[[soup], []]):
            incomplete = scraper.gather_data(process=False, descriptions=True)
        self.assertIn("raiffeisen_international1", incomplete)

    def test_failed_search_is_distinct_from_successful_empty_acquisition(self):
        scraper = KarriereAT(driver="", keywords={"titlewords": ["sales"], "locations": []})
        with patch.object(http, "requests_responses_with_cookies", return_value=[]):
            with self.assertRaisesRegex(RuntimeError, "Acquisition failed"):
                scraper.gather_data(process=False, descriptions=True)
        with patch.object(http, "requests_responses_with_cookies", return_value=[response([])]):
            self.assertEqual(scraper.gather_data(process=False, descriptions=True), {})

    def test_profile_location_changes_do_not_disable_raw_retention_protection(self):
        class Source:
            source = "test"
            postings = {str(i): {"title": "Sales", "company": "Company", "description": "Details", "source": "test"} for i in range(10)}

            def __init__(self, **kwargs):
                self.steps = (Step("all", self.collect),)

            def collect(self, records, config):
                return self.postings

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            run_universal_scrape_flow(path=folder, scrapers=[Source], locations_primary=["Vienna"])
            Source.postings = {"0": {"title": "Sales", "company": "Company", "description": "Details", "source": "test"}}
            with self.assertRaisesRegex(ValueError, "quality gate"):
                run_universal_scrape_flow(path=folder, scrapers=[Source], locations_primary=["London"],
                    minimum_source_retention={"test": .5})
            with self.assertRaisesRegex(ValueError, "quality gate"):
                run_universal_scrape_flow(path=folder, scrapers=[Source],
                    extra_keywords={"banned_words": ["director"]},
                    minimum_source_retention={"test": .5})


MANAGER_RECORD = {
    "id": "1", "source": "test", "url": "https://example.test/1",
    "title": "Facilities Manager", "company": "Company",
    "description": "Office upkeep and cleaning routines.",
}
POLICY_FIELDS = ("points", "keywords", "role_families", "language_adjustment",
                 "language_excluded", "profile_excluded")


def single_source(record):
    class Source:
        source = "test"

        def __init__(self, **kwargs):
            self.steps = (Step("all", self.collect),)

        def collect(self, records, config):
            return {"1": dict(record)}

    return Source


class UniversalAnnotationTests(unittest.TestCase):
    """B31: universal stores every posting, annotated, and profiles own policy."""

    def store(self, record):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            raw = run_universal_scrape_flow(path=folder, scrapers=[single_source(record)])
            stored = json.loads((Path(folder) / "postings_history.json").read_text())
        return raw, stored

    def test_profile_rejected_posting_is_still_stored_in_universal(self):
        raw, stored = self.store(MANAGER_RECORD)

        self.assertFalse(is_candidate(MANAGER_RECORD, {}))
        self.assertEqual(raw["1"]["title"], "Facilities Manager")
        self.assertIn("1", stored)

    def test_stored_posting_carries_the_annotations_and_no_policy_field(self):
        _raw, stored = self.store(MANAGER_RECORD)
        posting = stored["1"]

        self.assertEqual(UNIVERSAL_POSTINGS.check(stored), [])
        self.assertEqual(posting["language"], "en")
        self.assertEqual(posting["guessed_required_languages"], {})
        for field in POLICY_FIELDS:
            self.assertNotIn(field, posting)

    def test_stored_posting_keeps_collection_provenance(self):
        record = {**MANAGER_RECORD, "matched_titlewords": ["sales"]}
        _raw, stored = self.store(record)

        self.assertEqual(UNIVERSAL_POSTINGS.check(stored), [])
        self.assertEqual(stored["1"]["matched_titlewords"], ["sales"])
        self.assertEqual(stored["1"]["language"], "en")

    def test_derived_annotations_replace_but_absent_keys_keep_stored(self):
        previous = {
            "recomputed": {"language": "de", "guessed_required_languages": {"de": 1}},
            "omitted": {"language": "de", "guessed_required_languages": {"de": 1}},
        }
        current = {
            "recomputed": {"language": "", "guessed_required_languages": None},
            "omitted": {"title": "Facilities Manager"},
        }
        history = merge_observations(current, previous)

        self.assertEqual(history["recomputed"]["language"], "")
        self.assertIsNone(history["recomputed"]["guessed_required_languages"])
        self.assertEqual(history["omitted"]["language"], "de")
        self.assertEqual(history["omitted"]["guessed_required_languages"], {"de": 1})
