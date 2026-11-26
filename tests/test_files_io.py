"""Tests for atomic writes and UTC timestamps in the file layer (B30)."""

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from jobscraping.io import files_io


class _FixedUTCClock:
    """Stand-in for `datetime` that answers differently for local and UTC."""

    @staticmethod
    def now(tz=None):
        if tz is None:
            return datetime(2024, 1, 2, 5, 4, 5)
        return datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)


class SaveDataSafetyTests(unittest.TestCase):
    def setUp(self):
        self._folder = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.folder = Path(self._folder.name)
        self.target = self.folder / "postings.json"
        self.tmp = self.target.with_name(self.target.name + ".tmp")
        self.addCleanup(self._folder.cleanup)

    def test_previous_file_survives_a_serialization_failure(self):
        self.target.write_text('{"old": 1}', encoding="utf-8")

        with self.assertRaises(TypeError):
            files_io.save_data({"bad": object()}, path=str(self.folder) + "/",
                               name="postings", with_timestamp=False)

        self.assertEqual(json.loads(self.target.read_text(encoding="utf-8")),
                         {"old": 1})
        self.assertFalse(self.tmp.exists())

    def test_previous_file_survives_a_replace_failure(self):
        self.target.write_text('{"old": 1}', encoding="utf-8")

        with patch.object(files_io.os, "replace", side_effect=OSError("disk")), \
                self.assertRaises(OSError):
            files_io.save_data({"new": 2}, path=str(self.folder) + "/",
                               name="postings", with_timestamp=False)

        self.assertEqual(json.loads(self.target.read_text(encoding="utf-8")),
                         {"old": 1})
        self.assertFalse(self.tmp.exists())

    def test_successful_write_replaces_the_target_and_returns_its_path(self):
        written = files_io.save_data({"new": 2}, path=str(self.folder) + "/",
                                     name="postings", with_timestamp=False)

        self.assertEqual(written, self.target)
        self.assertEqual(json.loads(self.target.read_text(encoding="utf-8")),
                         {"new": 2})
        self.assertFalse(self.tmp.exists())


class SaveListSafetyTests(unittest.TestCase):
    def setUp(self):
        self._folder = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.folder = Path(self._folder.name)
        self.target = self.folder / "list.json"
        self.tmp = self.target.with_name(self.target.name + ".tmp")
        self.addCleanup(self._folder.cleanup)

    def test_previous_file_survives_a_serialization_failure(self):
        files_io.save_list([{"old": 1}], str(self.target))

        with self.assertRaises(TypeError):
            files_io.save_list([object()], str(self.target))

        self.assertEqual(json.loads(self.target.read_text(encoding="utf-8")),
                         [{"old": 1}])
        self.assertFalse(self.tmp.exists())

    def test_previous_file_survives_a_replace_failure(self):
        files_io.save_list([{"old": 1}], str(self.target))

        with patch.object(files_io.os, "replace", side_effect=OSError("disk")), \
                self.assertRaises(OSError):
            files_io.save_list([{"new": 2}], str(self.target))

        self.assertEqual(json.loads(self.target.read_text(encoding="utf-8")),
                         [{"old": 1}])
        self.assertFalse(self.tmp.exists())


class TimestampTests(unittest.TestCase):
    def test_timestamped_names_use_utc(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder, \
                patch.object(files_io, "datetime", _FixedUTCClock):
            written = files_io.save_data({"a": 1}, path=str(folder) + "/",
                                         name="run", with_timestamp=True)

        self.assertEqual(written.name, "run_2024-01-02-03-04-05.json")


if __name__ == "__main__":
    unittest.main()
