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

from jobscraping.scrapers import scrape
from jobscraping.scrapers.sites import KarriereAT, Raiffeisen


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
            patch.object(scrape.requests, "Session", return_value=session),
            patch.object(scrape.time, "sleep"),
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


class RaiffeisenFixtureParsingTests(unittest.TestCase):
    def parse(self):
        session = FixtureSession()
        scraper = Raiffeisen(
            driver="",
            keywords={"titlewords": ["sales"], "locations": []},
            date_day="2026-11-23",
        )
        with (
            patch.object(scrape.requests, "Session", return_value=session),
            patch.object(scrape.time, "sleep"),
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


if __name__ == "__main__":
    unittest.main()
