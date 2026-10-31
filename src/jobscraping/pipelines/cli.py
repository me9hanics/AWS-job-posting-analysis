"""Command-line arguments shared by the collection scripts."""

import argparse
from datetime import date


def _excel_days(value):
    try:
        days = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if days < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return days


def _date_day(value):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a valid date in YYYY-MM-DD format") from exc
    return parsed.isoformat()


def parse_collection_args(argv=None):
    parser = argparse.ArgumentParser(description="Collect job postings and generate Excel output.", allow_abbrev=False)
    parser.add_argument(
        "--excel-days", type=_excel_days, metavar="DAYS",
        help="Highlight postings first collected within this many days in Excel.",
    )
    parser.add_argument(
        "--date-day", type=_date_day, metavar="YYYY-MM-DD",
        help="Set the collection date; defaults to the current time minus BUSINESS_DAY_SHIFT.",
    )
    return parser.parse_args(argv)
