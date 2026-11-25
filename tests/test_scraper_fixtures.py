"""Parser parity for captured site payloads.

The fixtures under ``tests/fixtures/<site>/`` are trimmed samples captured from
the live sites on 2026-11-23 (see the B05 ticket). The HTTP session is replaced
by ``FixtureSession``, which serves those files and raises on any URL it does
not know, so these tests fail if the code under test tries to reach the network.
"""

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bs4 import BeautifulSoup

from jobscraping.scrapers import http
from jobscraping.scrapers import KarriereAT, Raiffeisen
from jobscraping.specs.postings import COLLECTED_POSTINGS, DISCOVERED_POSTINGS


FIXTURES = Path(__file__).parent / "fixtures"
KARRIERE_LISTING = FIXTURES / "karriere" / "listing.json"
KARRIERE_DETAIL = FIXTURES / "karriere" / "detail.json"
RAIFFEISEN_LISTING = FIXTURES / "raiffeisen" / "listing.html"
RAIFFEISEN_DETAIL = FIXTURES / "raiffeisen" / "detail.html"

EMPTY_KARRIERE_PAGE = json.dumps(
    {"data": {"jobsSearchList": {"activeItems": {"items": []}}}}
)


def json_response(text, status_code=200):
    return SimpleNamespace(text=text, content=text.encode("utf-8"),
                           status_code=status_code, cookies=[])


class FixtureSession:
    """Stand-in for ``requests.Session`` that only knows the captured endpoints."""

    def __init__(self):
        self.cookies = SimpleNamespace(set=lambda *_args: None)
        self.requested_urls = []

    def get(self, url, **_kwargs):
        self.requested_urls.append(url)
        if "karriere.at/jobs?keywords=" in url:
            body = KARRIERE_LISTING.read_text(encoding="utf-8")
            if len([u for u in self.requested_urls if "karriere.at/jobs?keywords=" in u]) > 1:
                body = EMPTY_KARRIERE_PAGE
            return json_response(body)
        if url.startswith("https://www.karriere.at/jobs/"):
            return json_response(KARRIERE_DETAIL.read_text(encoding="utf-8"))
        if url.startswith("https://jobs.rbinternational.com/search/"):
            return json_response(RAIFFEISEN_LISTING.read_text(encoding="utf-8"))
        if url.startswith("https://jobs.rbinternational.com/"):
            return json_response(RAIFFEISEN_DETAIL.read_text(encoding="utf-8"))
        raise AssertionError(f"Unexpected network request: {url}")


class KarriereFixtureParsingTests(unittest.TestCase):
    def parse(self):
        session = FixtureSession()
        scraper = KarriereAT(
            driver="",
            keywords={"titlewords": ["sales"], "locations": ["wien-und-umgebung"]},
            date_day="2026-11-23",
        )
        with (
            patch.object(http.requests, "Session", return_value=session),
            patch.object(http.time, "sleep"),
        ):
            postings = scraper.gather_data(process=False, descriptions=True)
        return postings, session

    def test_listing_and_detail_fixtures_produce_expected_posting(self):
        postings, session = self.parse()
        self.assertEqual(
            session.requested_urls,
            [
                "https://www.karriere.at/jobs?keywords=sales&location=wien und umgebung&page=1",
                "https://www.karriere.at/jobs?keywords=sales&location=wien und umgebung&page=2",
                "https://www.karriere.at/jobs/10035272",
                "https://www.karriere.at/jobs/10029573",
            ],
        )

        posting = postings["karriere.at10035272"]
        self.assertEqual(posting["id"], "10035272")
        self.assertEqual(posting["source"], "karriere.at")
        self.assertEqual(posting["title"], "Key Account Manager Amazon & Marktplätze (m/w/d)")
        self.assertEqual(posting["company"], "Windhager Home & Garden")
        self.assertEqual(posting["locations"], ["Thalgau"])
        self.assertEqual(posting["date"], "Gestern veröffentlicht")
        self.assertEqual(posting["salary"], "ab 50.000 € jährlich")
        self.assertEqual(posting["employmentTypes"], "Vollzeit")
        self.assertIs(posting["isActive"], True)
        self.assertIs(posting["isHomeOffice"], False)
        self.assertEqual(posting["url"], "https://www.karriere.at/jobs/10035272")
        self.assertEqual(posting["matched_titlewords"], ["sales"])

        description = posting["description"]
        self.assertIn("Amazon Vendor- und Seller-Accounts", description)
        self.assertIn("Mehrjährige E-Commerce-Erfahrung", description)
        self.assertNotIn("<p>", description)

    def test_listing_fixture_keeps_second_posting_and_relative_date(self):
        postings, _ = self.parse()

        posting = postings["karriere.at10029573"]
        self.assertEqual(posting["title"], "Vertriebsinnendienst (m/w/d)")
        self.assertEqual(posting["company"], "Moderne Verpackung")
        self.assertEqual(posting["locations"], ["Jeging"])
        self.assertEqual(posting["date"], "vor 4 Tagen veröffentlicht")
        self.assertEqual(posting["matched_titlewords"], ["sales"])


class KarriereStepTests(unittest.TestCase):
    """The declared steps are the new path; ``gather_data`` delegates to them."""

    def scraper(self):
        return KarriereAT(
            driver="",
            keywords={"titlewords": ["sales"], "locations": ["wien-und-umgebung"]},
            date_day="2026-11-23",
        )

    def config(self, **overrides):
        values = {"cached_postings": {}, "cache_mode": None,
                  "cache_hit_predicate": None}
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_steps_are_declared_in_order_with_their_specs(self):
        steps = self.scraper().steps
        self.assertEqual([step.name for step in steps], ["listings", "details"])
        self.assertIs(steps[0].output_spec, DISCOVERED_POSTINGS)
        self.assertIs(steps[1].input_spec, DISCOVERED_POSTINGS)
        self.assertIs(steps[1].output_spec, COLLECTED_POSTINGS)

    def test_listings_returns_identity_records_without_descriptions(self):
        session = FixtureSession()
        with (
            patch.object(http.requests, "Session", return_value=session),
            patch.object(http.time, "sleep"),
        ):
            postings = self.scraper().listings({}, self.config())

        self.assertEqual(
            sorted(postings), ["karriere.at10029573", "karriere.at10035272"]
        )
        posting = postings["karriere.at10029573"]
        self.assertEqual(posting["source"], "karriere.at")
        self.assertEqual(posting["url"], "https://www.karriere.at/jobs/10029573")
        self.assertNotIn("description", posting)
        self.assertNotIn(
            "https://www.karriere.at/jobs/10029573", session.requested_urls
        )

    def test_details_skips_cached_ids_and_merges_the_hit(self):
        scraper = self.scraper()
        session = FixtureSession()
        cached = {
            "karriere.at10035272": {
                "title": "Cached title",
                "company": "Windhager Home & Garden",
                "description": "Cached description",
            }
        }
        config = self.config(cached_postings=cached, cache_mode="id-only")
        with (
            patch.object(http.requests, "Session", return_value=session),
            patch.object(http.time, "sleep"),
        ):
            result = scraper.details(scraper.listings({}, config), config)

        hit = result["karriere.at10035272"]
        self.assertEqual(hit["description"], "Cached description")
        self.assertEqual(
            hit["title"], "Key Account Manager Amazon & Marktplätze (m/w/d)"
        )
        detail_urls = [
            url for url in session.requested_urls
            if url.startswith("https://www.karriere.at/jobs/")
        ]
        self.assertEqual(detail_urls, ["https://www.karriere.at/jobs/10029573"])


class RaiffeisenFixtureParsingTests(unittest.TestCase):
    def parse(self):
        session = FixtureSession()
        scraper = Raiffeisen(
            driver="",
            keywords={"titlewords": ["sales"], "locations": []},
            date_day="2026-11-23",
        )
        with (
            patch.object(http.requests, "Session", return_value=session),
            patch.object(http.time, "sleep"),
        ):
            postings = scraper.gather_data(process=False, descriptions=True)
        return postings, session

    def test_listing_fixture_produces_prefixed_ids(self):
        postings, _ = self.parse()
        self.assertEqual(
            sorted(postings),
            [
                "raiffeisen_international1364426457",
                "raiffeisen_international1373093957",
            ],
        )
        posting = postings["raiffeisen_international1364426457"]
        self.assertEqual(
            posting["title"],
            "Operations Manager - Digital Investment Platform (w/m/x) - Savity",
        )
        self.assertEqual(
            posting["url"],
            "https://jobs.rbinternational.com/raiffeisencapitalmgmt/job/"
            "Wien-Operations-Manager-Digital-Investment-Platform-%28wmx%29-Savity-1190/1364426457/",
        )
        self.assertEqual(posting["company"], "Raiffeisen International")
        self.assertEqual(posting["source"], "raiffeisen_international")
        self.assertEqual(posting["matched_titlewords"], ["sales"])
        self.assertEqual(posting["collected_on"], "2026-11-23")

    def test_detail_fixture_fills_description_sections(self):
        postings, _ = self.parse()
        posting = postings["raiffeisen_international1373093957"]

        self.assertIn(
            "Eigenständige Bearbeitung und Koordination operativer Aufgaben",
            posting["description"],
        )
        self.assertIn("Abgeschlossenes wirtschaftliches, IT-nahes", posting["requirements"])
        self.assertIn("Erfahrung im Wertpapier-", posting["nice_to_have"])
        self.assertIn("Ein hohes Maß an Eigenverantwortung", posting["benefits"])
        self.assertIsNone(posting["salary_guessed"])


class HttpRequestParsingTests(unittest.TestCase):
    """The HTTP path issues one request and parses the payload, without network."""

    def test_requests_responses_parses_the_listing_fixture_into_a_soup(self):
        session = FixtureSession()
        url = "https://jobs.rbinternational.com/search/?q=sales&page=1"
        with (
            patch.object(http.requests, "Session", return_value=session),
            patch.object(http.time, "sleep"),
        ):
            soups = http.requests_responses(
                [url], return_kind="soups", https=True, wait_time=0.3
            )

        self.assertEqual(session.requested_urls, [url])
        self.assertEqual(len(soups), 1)
        self.assertIsInstance(soups[0], BeautifulSoup)
        self.assertEqual(len(soups[0].select("a.jobTitle-link")), 2)


class RaiffeisenHelperParsingTests(unittest.TestCase):
    """Drive Raiffeisen's separable parse helpers without HTTP or a browser."""

    def setUp(self):
        self.scraper = Raiffeisen(
            driver="",
            keywords={"titlewords": ["sales"], "locations": []},
            date_day="2026-11-23",
        )

    def soup(self, path):
        return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")

    def test_process_posting_soups_parses_the_listing_fixture(self):
        postings = self.scraper._process_posting_soups(
            [self.soup(RAIFFEISEN_LISTING)],
            self.scraper.rules["gather_data_selector"],
        )

        self.assertEqual(
            sorted(postings),
            [
                "raiffeisen_international1364426457",
                "raiffeisen_international1373093957",
            ],
        )
        posting = postings["raiffeisen_international1364426457"]
        self.assertEqual(
            posting["title"],
            "Operations Manager - Digital Investment Platform (w/m/x) - Savity",
        )
        self.assertEqual(
            posting["url"],
            "https://jobs.rbinternational.com/raiffeisencapitalmgmt/job/"
            "Wien-Operations-Manager-Digital-Investment-Platform-%28wmx%29-Savity-1190/1364426457/",
        )
        self.assertEqual(posting["company"], "Raiffeisen International")
        self.assertEqual(posting["source"], "raiffeisen_international")
        self.assertNotIn("collected_on", posting)

    def test_get_descriptions_from_soups_parses_the_detail_fixture(self):
        descriptions = self.scraper._get_descriptions_from_soups(
            {"raiffeisen_international1373093957": self.soup(RAIFFEISEN_DETAIL)}
        )

        details = descriptions["raiffeisen_international1373093957"]
        self.assertIn(
            "Eigenständige Bearbeitung und Koordination operativer Aufgaben",
            details["description"],
        )
        self.assertIn("Abgeschlossenes wirtschaftliches, IT-nahes", details["requirements"])
        self.assertIn("Erfahrung im Wertpapier-", details["nice_to_have"])
        self.assertIn("Ein hohes Maß an Eigenverantwortung", details["benefits"])
        self.assertIsNone(details["salary_guessed"])


if __name__ == "__main__":
    unittest.main()
