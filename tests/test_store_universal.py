"""Tests for the incomplete-run artifact's UTC filename (B30)."""

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from jobscraping.pipelines import store_universal


class _FixedUTCClock:
    @staticmethod
    def now(tz=None):
        if tz is None:
            return datetime(2024, 1, 2, 5, 4, 5)
        return datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)


class SaveIncompleteRunTests(unittest.TestCase):
    def test_filename_uses_utc(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            with patch.object(store_universal, "datetime", _FixedUTCClock):
                store_universal.save_incomplete_run({}, folder, RuntimeError("boom"))

            names = sorted(path.name for path in Path(folder).iterdir())

        self.assertEqual(names,
                         ["incomplete_run_2024-01-02-03-04-05-000000.json"])


if __name__ == "__main__":
    unittest.main()
