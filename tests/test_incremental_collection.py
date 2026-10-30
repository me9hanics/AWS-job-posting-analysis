import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from jobscraping.pipelines import collecting
from jobscraping.processing.postings_utils import split_cached_postings, unify_postings
from jobscraping.scrapers import scrape
from jobscraping.scrapers.sites import KarriereAT
from schedule.dani_collect import dani_cache_hit_by_id
from schedule import dani_collect, legal_collect, tech_collect, tn_collect


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self.text = json.dumps(payload)
        self.status_code = status_code
        self.cookies = []


class IncrementalCollectionTests(unittest.TestCase):
    def test_requests_with_cookies_stops_on_success_condition(self):
        responses = [
            _FakeResponse({"items": [1]}),
            _FakeResponse({"items": []}),
            _FakeResponse({"items": [3]}),
        ]
        calls = []

        class _Session:
            cookies = SimpleNamespace(set=lambda *_args: None)

            def get(self, url, headers, timeout):
                calls.append(url)
                return responses[len(calls) - 1]

        with patch.object(scrape.requests, "Session", _Session):
            collected = scrape.requests_responses_with_cookies(
                base_url="https://example.test/jobs",
                pages=["?page=1", "?page=2", "?page=3"],
                base_path="/jobs",
                wait_time=0,
                stop_condition=lambda response: not json.loads(response.text)["items"],
            )

        self.assertEqual(len(calls), 2)
        self.assertEqual(collected, responses[:2])

    def test_requests_with_cookies_retries_transient_http_status(self):
        responses = [
            _FakeResponse({}, status_code=504),
            _FakeResponse({"items": [1]}),
        ]
        calls = []

        class _Session:
            cookies = SimpleNamespace(set=lambda *_args: None)

            def get(self, url, headers, timeout):
                calls.append((url, timeout))
                return responses[len(calls) - 1]

        with patch.object(scrape.requests, "Session", _Session):
            collected = scrape.requests_responses_with_cookies(
                base_url="https://example.test/jobs",
                pages=["?page=1"],
                base_path="/jobs",
                wait_time=0,
            )

        self.assertEqual(len(calls), 2)
        self.assertEqual(collected, responses[1:])

    def test_requests_with_cookies_can_continue_after_non_retryable_error(self):
        responses = [
            _FakeResponse({}, status_code=404),
            _FakeResponse({"items": [2]}),
        ]
        calls = []

        class _Session:
            cookies = SimpleNamespace(set=lambda *_args: None)

            def get(self, url, headers, timeout):
                calls.append(url)
                return responses[len(calls) - 1]

        with patch.object(scrape.requests, "Session", _Session):
            collected = scrape.requests_responses_with_cookies(
                base_url="https://example.test/jobs",
                pages=["/1", "/2"],
                base_path="/jobs",
                wait_time=0,
                continue_on_http_error=True,
            )

        self.assertEqual(len(calls), 2)
        self.assertEqual(collected, responses[1:])

    def test_requests_with_cookies_raises_after_transient_retry_fails(self):
        responses = [
            _FakeResponse({}, status_code=504),
            _FakeResponse({}, status_code=504),
        ]
        calls = []

        class _Session:
            cookies = SimpleNamespace(set=lambda *_args: None)

            def get(self, url, headers, timeout):
                calls.append(url)
                return responses[len(calls) - 1]

        with (
            patch.object(scrape.requests, "Session", _Session),
            self.assertRaisesRegex(RuntimeError, "504"),
        ):
            scrape.requests_responses_with_cookies(
                base_url="https://example.test/jobs",
                pages=["?page=1"],
                base_path="/jobs",
                wait_time=0,
                raise_on_retry_failure=True,
            )

        self.assertEqual(len(calls), 2)

    def test_id_only_cache_uses_fresh_listing_fields_and_cached_processed_fields(self):
        discovered = {
            "site-1": {
                "title": "Fresh title",
                "company": "",
                "locations": ["Vienna"],
                "collected_on": "2026-09-29",
            },
            "site-2": {"title": "New posting"},
        }
        cached = {
            "site-1": {
                "title": "Old title",
                "company": "Cached company",
                "locations": ["Old location"],
                "description": "Cached description",
                "keywords": ["cached"],
                "points": 4.2,
            }
        }

        hits, misses = split_cached_postings(
            discovered,
            cached_postings=cached,
            cache_mode="id-only",
        )

        self.assertEqual(misses, {"site-2": {"title": "New posting"}})
        self.assertEqual(hits["site-1"]["title"], "Fresh title")
        self.assertEqual(hits["site-1"]["company"], "Cached company")
        self.assertEqual(hits["site-1"]["locations"], ["Vienna"])
        self.assertEqual(hits["site-1"]["description"], "Cached description")
        self.assertEqual(hits["site-1"]["keywords"], ["cached"])
        self.assertEqual(hits["site-1"]["points"], 4.2)

    def test_cache_hit_predicate_can_turn_an_existing_id_into_a_miss(self):
        hits, misses = split_cached_postings(
            {"site-1": {"title": "Posting"}},
            cached_postings={"site-1": {"description": "Cached"}},
            cache_mode="id-only",
            cache_hit_predicate=lambda _id, _fresh, _cached: False,
        )

        self.assertEqual(hits, {})
        self.assertEqual(list(misses), ["site-1"])

    def test_unknown_cache_mode_is_explicitly_unimplemented(self):
        with self.assertRaisesRegex(NotImplementedError, "content-hash"):
            split_cached_postings({}, cache_mode="content-hash")

    def test_dani_id_cache_is_limited_to_configured_sources(self):
        self.assertTrue(
            dani_cache_hit_by_id(
                "karriere.at1",
                {"source": "karriere.at"},
                {
                    "title": "Cached title",
                    "company": "Cached company",
                    "description": "Cached description",
                },
            )
        )
        self.assertFalse(
            dani_cache_hit_by_id(
                "karriere.at1",
                {"source": "karriere.at"},
                {
                    "title": "Cached title",
                    "company": "Cached company",
                    "description": "",
                },
            )
        )
        self.assertFalse(
            dani_cache_hit_by_id(
                "raiffeisen_international1",
                {"source": "raiffeisen_international"},
                {"description": "Cached"},
            )
        )

    def test_profile_entrypoints_forward_their_cache_policy(self):
        policies = [
            (dani_collect, dani_collect.get_dani_postings, "id-only"),
            (tn_collect, tn_collect.get_tn_postings, "id-only"),
            (legal_collect, legal_collect.get_legal_postings, None),
            (tech_collect, tech_collect.get_tech_postings, None),
        ]

        for module, collect, expected_mode in policies:
            with self.subTest(module=module.__name__):
                received = {}

                def _get_postings(**kwargs):
                    received.update(kwargs)
                    return {"results": {}, "added": {}, "removed": {}}

                with (
                    patch.object(module, "get_postings", _get_postings),
                    patch.object(
                        module,
                        "generate_outputs",
                        return_value={"excel_file_path": None},
                    ),
                ):
                    collect(path_excel=None)

                self.assertIn("cache_mode", received)
                self.assertEqual(received["cache_mode"], expected_mode)
                self.assertEqual(
                    received["required_fields_by_source"],
                    {"karriere.at": ("description", "company")},
                )
                self.assertEqual(
                    received["minimum_source_retention"],
                    {"karriere.at": 0.5},
                )

    def test_tn_id_cache_is_limited_to_karriere(self):
        self.assertTrue(
            tn_collect.tn_cache_hit_by_id(
                "karriere.at1",
                {"source": "karriere.at"},
                {
                    "title": "Cached title",
                    "company": "Cached company",
                    "description": "Cached description",
                },
            )
        )
        self.assertFalse(
            tn_collect.tn_cache_hit_by_id(
                "raiffeisen_international1",
                {"source": "raiffeisen_international"},
                {"description": "Cached"},
            )
        )

    def test_karriere_cache_fetches_and_processes_only_misses(self):
        search_payload = {
        "data": {
            "jobsSearchList": {
                "activeItems": {
                    "items": [
                        {
                            "jobsItem": {
                                "id": 1,
                                "title": "Fresh cached title",
                                "company": {"name": "Cached company"},
                                "locations": [{"name": "Vienna"}],
                                "salary": "",
                                "isActive": True,
                                "isHomeOffice": False,
                                "employmentTypes": [],
                                "link": "https://www.karriere.at/jobs/1",
                                "snippet": "Fresh snippet",
                                "date": "2026-09-29",
                            }
                        },
                        {
                            "jobsItem": {
                                "id": 2,
                                "title": "New title",
                                "company": {"name": "New company"},
                                "locations": [{"name": "Vienna"}],
                                "salary": "",
                                "isActive": True,
                                "isHomeOffice": False,
                                "employmentTypes": [],
                                "link": "https://www.karriere.at/jobs/2",
                                "snippet": "New snippet",
                                "date": "2026-09-29",
                            }
                        },
                    ]
                }
            }
        }
        }
        detail_payload = {
        "data": {
            "jobDetailContent": {
                "jobContent": {"text": "<p>New description</p>"},
                "jobHeader": {"job": {"id": 2}},
            }
        }
        }
        request_pages = []

        def _requests_with_cookies(*_args, **kwargs):
            request_pages.append(kwargs["pages"])
            if len(request_pages) == 1:
                return [_FakeResponse(search_payload)]
            return [_FakeResponse(detail_payload)]

        scraper = KarriereAT(
            driver="",
            keywords={
                "titlewords": ["sales"],
                "locations": ["vienna"],
                "banned_words": [],
                "banned_capital_words": [],
                "description_keywords_order": [],
            },
            rankings={},
        )
        processed_ids = []

        def _process_data(postings, **_kwargs):
            processed_ids.extend(postings)
            for posting in postings.values():
                posting["points"] = 1
            return postings

        with (
            patch.object(scrape, "requests_responses_with_cookies", _requests_with_cookies),
            patch.object(scraper, "_process_data", _process_data),
        ):
            results = scraper.gather_data(
                descriptions=True,
                cached_postings={
                    "karriere.at1": {
                        "title": "Old cached title",
                        "description": "Cached description",
                        "keywords": ["cached"],
                        "points": 7,
                    }
                },
                cache_mode="id-only",
            )

        self.assertEqual(request_pages[1], ["/2"])
        self.assertEqual(processed_ids, ["karriere.at2"])
        self.assertEqual(results["karriere.at1"]["title"], "Fresh cached title")
        self.assertEqual(results["karriere.at1"]["description"], "Cached description")
        self.assertEqual(results["karriere.at1"]["points"], 7)
        self.assertEqual(results["karriere.at2"]["description"], "New description")
        self.assertEqual(results["karriere.at2"]["points"], 1)

    def test_karriere_does_not_process_listing_when_detail_is_missing(self):
        search_payload = {
            "data": {
                "jobsSearchList": {
                    "activeItems": {
                        "items": [
                            {
                                "jobsItem": {
                                    "id": 1,
                                    "title": "Incomplete posting",
                                    "company": {"name": "Company"},
                                    "locations": [{"name": "Vienna"}],
                                    "salary": "",
                                    "isActive": True,
                                    "isHomeOffice": False,
                                    "employmentTypes": [],
                                    "link": "https://www.karriere.at/jobs/1",
                                    "snippet": "Snippet",
                                    "date": "2026-10-21",
                                }
                            }
                        ]
                    }
                }
            }
        }
        request_count = 0

        def _requests_with_cookies(*_args, **_kwargs):
            nonlocal request_count
            request_count += 1
            return [_FakeResponse(search_payload)] if request_count == 1 else []

        scraper = KarriereAT(
            driver="",
            keywords={
                "titlewords": ["sales"],
                "locations": ["vienna"],
                "banned_words": [],
                "banned_capital_words": [],
                "description_keywords_order": [],
            },
            rankings={},
        )

        with (
            patch.object(scrape, "requests_responses_with_cookies", _requests_with_cookies),
            patch.object(scraper, "_process_data", return_value={}) as process_data,
        ):
            results = scraper.gather_data(descriptions=True)

        self.assertEqual(results, {})
        process_data.assert_called_once_with(
            {}, transformations=[], description_key="description"
        )

    def test_unify_postings_can_target_history_and_current_only(self):
        history = {
            "old": {
                "title": "Old",
                "collected_on": "2026-09-20",
            }
        }
        unrelated = {
            "unrelated": {
                "title": "Unrelated",
                "collected_on": "2026-09-21",
            }
        }
        current = {
            "new": {
                "title": "New",
                "collected_on": "2026-09-29",
            }
        }
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "postings_history.json").write_text(
                json.dumps(history), encoding="utf-8"
            )
            (temp_path / "newly_added_postings.json").write_text(
                json.dumps(unrelated), encoding="utf-8"
            )

            all_files = unify_postings(folder_path=str(temp_path))
            targeted = unify_postings(
                postings=current,
                folder_path=str(temp_path),
                merge_with_history=True,
            )

        self.assertEqual(set(all_files), {"old", "unrelated"})
        self.assertEqual(set(targeted), {"old", "new"})

    def test_unify_postings_repairs_derived_fields_of_incomplete_history(self):
        history = {
            "karriere.at1": {
                "title": "Posting",
                "company": "Company",
                "description": "",
                "keywords": [],
                "language": None,
                "points": 0.5,
                "collected_on": "2026-10-20",
                "first_collected_on": "2026-10-20",
                "last_collected_on": "2026-10-20",
            }
        }
        repaired = {
            "karriere.at1": {
                "title": "Posting",
                "company": "Company",
                "description": "Complete description",
                "keywords": ["sales"],
                "language": "en",
                "points": 4.5,
                "collected_on": "2026-10-21",
            }
        }

        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "postings_history.json").write_text(
                json.dumps(history), encoding="utf-8"
            )
            merged = unify_postings(
                postings=repaired,
                folder_path=str(temp_path),
                merge_with_history=True,
            )

        posting = merged["karriere.at1"]
        self.assertEqual(posting["description"], "Complete description")
        self.assertEqual(posting["keywords"], ["sales"])
        self.assertEqual(posting["language"], "en")
        self.assertEqual(posting["points"], 4.5)
        self.assertEqual(posting["first_collected_on"], "2026-10-20")
        self.assertEqual(posting["last_collected_on"], "2026-10-21")

    def test_get_postings_loads_history_before_scraping_when_cache_is_enabled(self):
        cached = {
            "site-1": {
                "title": "Cached",
                "company": "Company",
                "locations": ["Vienna"],
                "points": 1,
                "collected_on": "2026-09-28",
            }
        }
        current = {
            "site-1": {
                **cached["site-1"],
                "title": "Fresh",
                "collected_on": "2026-09-29",
            }
        }
        received = {}

        def _scrape_sites(**kwargs):
            received.update(kwargs)
            return current

        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "postings_history.json").write_text(
                json.dumps(cached), encoding="utf-8"
            )
            with patch.object(collecting, "scrape_sites", _scrape_sites):
                collecting.get_postings(
                    keywords={"titlewords": []},
                    rankings={},
                    path=f"{temp_path}/",
                    threshold=None,
                    cache_mode="id-only",
                )

        self.assertEqual(received["cached_postings"], cached)
        self.assertEqual(received["cache_mode"], "id-only")

    def test_quality_gate_prevents_any_output_overwrite(self):
        incomplete = {
            "karriere.at1": {
                "title": "Posting",
                "company": "Company",
                "description": "",
                "locations": ["Vienna"],
                "source": "karriere.at",
                "points": 1,
                "collected_on": "2026-10-21",
            }
        }

        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp_dir:
            temp_path = Path(temp_dir)
            for filename in (
                "current_postings.json",
                "newly_added_postings.json",
                "postings_history.json",
            ):
                (temp_path / filename).write_text("{}", encoding="utf-8")

            with (
                patch.object(collecting, "scrape_sites", return_value=incomplete),
                patch.object(collecting.files_io, "save_data") as save_data,
                self.assertRaisesRegex(ValueError, "description=1"),
            ):
                collecting.get_postings(
                    keywords={"titlewords": []},
                    rankings={},
                    path=f"{temp_path}/",
                    threshold=None,
                    required_fields_by_source={
                        "karriere.at": ("description", "company")
                    },
                )

        save_data.assert_not_called()

    def test_quality_gate_rejects_large_source_count_drop(self):
        previous = {
            f"karriere.at{index}": {"source": "karriere.at"}
            for index in range(10)
        }
        current = {
            f"karriere.at{index}": {"source": "karriere.at"}
            for index in range(4)
        }

        with self.assertRaisesRegex(ValueError, "retained 4/10"):
            collecting.validate_postings_quality(
                current,
                previous_postings=previous,
                minimum_source_retention={"karriere.at": 0.5},
            )


if __name__ == "__main__":
    unittest.main()
