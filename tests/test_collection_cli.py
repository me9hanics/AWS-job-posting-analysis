import contextlib
import io
import time
import unittest
from unittest.mock import patch

from jobscraping.pipelines.cli import parse_collection_args
from jobscraping.pipelines.collecting import scrape_sites
from jobscraping.scrapers.sites import (
    BUSINESS_DAY_SHIFT,
    BaseScraper,
    KarriereAT,
    Raiffeisen,
)
from schedule import dani_collect, legal_collect, tech_collect, tn_collect


class CollectionCliTests(unittest.TestCase):
    def test_defaults_and_named_options(self):
        defaults = parse_collection_args([])
        self.assertIsNone(defaults.excel_days)
        self.assertIsNone(defaults.date_day)
        args = parse_collection_args(["--excel-days", "7", "--date-day", "2026-10-30"])
        self.assertEqual(args.excel_days, 7)
        self.assertEqual(args.date_day, "2026-10-30")
        self.assertEqual(parse_collection_args(["--excel-days", "0"]).excel_days, 0)

    def test_invalid_arguments_are_rejected(self):
        for argv in (
            ["7"], ["--excel-days", "-1"], ["--excel-days", "seven"],
            ["--excel-days"], ["--date-day", "2026-02-30"],
            ["--date-day", "30/10/2026"], ["--date-day", "20261030"],
            ["--date-day"], ["--unknown"],
        ):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    parse_collection_args(argv)
                self.assertEqual(error.exception.code, 2)

    def test_all_scripts_forward_options_before_collecting(self):
        for profile in (legal_collect, tn_collect, tech_collect, dani_collect):
            name = profile.__name__.split(".")[-1].replace("_collect", "")
            with self.subTest(profile=name), patch.object(
                profile, f"get_{name}_postings", side_effect=RuntimeError("stop before scraping")
            ) as collect, patch("sys.argv", [name, "--excel-days", "7", "--date-day", "2026-10-30"]):
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, "stop before scraping"):
                    profile.main()
                self.assertEqual(collect.call_args.kwargs["highlight_first_collected_days"], 7)
                self.assertEqual(collect.call_args.kwargs["date_day"], "2026-10-30")

    def test_all_scripts_reject_positional_days_without_collecting(self):
        for profile in (legal_collect, tn_collect, tech_collect, dani_collect):
            name = profile.__name__.split(".")[-1].replace("_collect", "")
            with self.subTest(profile=name), patch.object(profile, f"get_{name}_postings") as collect:
                with patch("sys.argv", [name, "7"]), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        profile.main()
                self.assertEqual(error.exception.code, 2)
                collect.assert_not_called()

    def test_profile_functions_forward_date_to_collection_pipeline(self):
        for profile in (legal_collect, tn_collect, tech_collect, dani_collect):
            name = profile.__name__.split(".")[-1].replace("_collect", "")
            with self.subTest(profile=name), patch.object(profile, "get_postings", return_value={}) as collect:
                with patch.object(profile, "generate_outputs", return_value={}):
                    getattr(profile, f"get_{name}_postings")(date_day="2026-10-30", path_excel=None)
                self.assertEqual(collect.call_args.kwargs["date_day"], "2026-10-30")


class CollectionDateTests(unittest.TestCase):
    def test_explicit_date_overrides_business_day_for_all_scrapers(self):
        for scraper_class in (BaseScraper, KarriereAT, Raiffeisen):
            with self.subTest(scraper=scraper_class.__name__):
                scraper = scraper_class(driver="", date_day="2026-10-30")
                self.assertEqual(scraper.business_day, "2026-10-30")
                self.assertEqual(scraper.day, scraper.time[:10])

    def test_default_date_uses_business_day_shift_across_midnight(self):
        now = time.mktime((2026, 10, 31, 3, 0, 0, 0, 0, -1))
        with patch("jobscraping.scrapers.sites.time.time", return_value=now):
            scraper = BaseScraper(driver="")
        self.assertEqual(scraper.day, "2026-10-31")
        self.assertEqual(scraper.business_day, time.strftime("%Y-%m-%d", time.localtime(now - BUSINESS_DAY_SHIFT)))
        self.assertEqual(scraper.business_day, "2026-10-30")

    def test_pipeline_passes_date_to_scrapers(self):
        class FakeScraper(BaseScraper):
            def __init__(self, **kwargs):
                super().__init__(driver="", **kwargs)

            def gather_data(self, **kwargs):
                return {"posting": {"collected_on": self.business_day}}

        results = scrape_sites(scrapers=[FakeScraper], date_day="2026-10-30")
        self.assertEqual(results["posting"]["collected_on"], "2026-10-30")


if __name__ == "__main__":
    unittest.main()
