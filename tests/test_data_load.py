"""Tests for the data-layer loading and writing seam (B26)."""

import json
import tempfile
import unittest
from pathlib import Path

from jobscraping.config.constants import SCHEMA_VERSION, VAULT_META_FILENAME
from jobscraping.data.load import (
    load_postings,
    load_vault_meta,
    save_json,
    save_posting_set,
    save_vault_meta,
)


class LoadPostingsTests(unittest.TestCase):
    def test_missing_file_loads_as_empty_mapping(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            self.assertEqual(load_postings(folder, "absent.json"), {})

    def test_stored_mapping_is_loaded_back(self):
        records = {"id-1": {"title": "Sales"}}
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            with open(Path(folder) / "postings.json", "w", encoding="utf-8") as file_obj:
                json.dump(records, file_obj)

            self.assertEqual(load_postings(folder, "postings.json"), records)


class SaveJsonTests(unittest.TestCase):
    def test_returns_the_written_path_with_content(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            written = save_json({"scope": "test"}, folder, "collection_scope.json")

            self.assertEqual(written, Path(folder) / "collection_scope.json")
            self.assertTrue(written.is_file())
            with open(written, encoding="utf-8") as file_obj:
                self.assertEqual(json.load(file_obj), {"scope": "test"})

    def test_timestamped_name_keeps_the_filename_prefix(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            written = save_json({"a": 1}, folder, "run", with_timestamp=True)

            self.assertEqual(written.parent, Path(folder))
            self.assertTrue(written.stem.startswith("run_"))
            self.assertTrue(written.is_file())


class SavePostingSetTests(unittest.TestCase):
    def test_mapping_records_are_written_and_path_returned(self):
        records = {"id-1": {"title": "Sales"}}
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            written = save_posting_set(records, folder, "current_postings.json")

            self.assertEqual(written, Path(folder) / "current_postings.json")
            with open(written, encoding="utf-8") as file_obj:
                self.assertEqual(json.load(file_obj), records)

    def test_list_records_also_write_vault_meta(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            save_posting_set([{"title": "Sales"}], folder, "run.json")

            meta = load_vault_meta(folder)
            self.assertEqual(meta["schema_version"], SCHEMA_VERSION)


class VaultMetaTests(unittest.TestCase):
    def test_missing_meta_loads_as_empty_mapping(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            self.assertEqual(load_vault_meta(folder), {})

    def test_meta_carries_schema_version_and_utc_timestamp(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            written = save_vault_meta(folder)

            self.assertEqual(written, Path(folder) / VAULT_META_FILENAME)
            with open(written, encoding="utf-8") as file_obj:
                meta = json.load(file_obj)
            self.assertEqual(meta["schema_version"], SCHEMA_VERSION)
            self.assertTrue(meta["updated_at"].endswith("+00:00"))

    def test_explicit_updated_at_is_preserved(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            save_vault_meta(folder, updated_at="2025-01-01T00:00:00+00:00")

            self.assertEqual(load_vault_meta(folder)["updated_at"],
                             "2025-01-01T00:00:00+00:00")

    def test_save_posting_set_writes_meta_next_to_the_posting_file(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            save_posting_set({"id-1": {"title": "Sales"}}, folder,
                             "postings_history.json")

            self.assertTrue((Path(folder) / VAULT_META_FILENAME).is_file())
            self.assertEqual(load_vault_meta(folder)["schema_version"],
                             SCHEMA_VERSION)

    def test_save_json_leaves_no_meta_beside_a_scope_file(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            save_json({"scope": "test"}, folder, "collection_scope.json")

            self.assertEqual(load_vault_meta(folder), {})
            self.assertEqual(sorted(path.name for path in Path(folder).iterdir()),
                             ["collection_scope.json"])


class LegacyFileTests(unittest.TestCase):
    def test_local_time_metadata_is_read_back_unchanged(self):
        legacy = {"id-1": {"title": "Sales", "collected_on": "2025-08-06 00:32:31"}}
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            with open(Path(folder) / "postings.json", "w", encoding="utf-8") as file_obj:
                json.dump(legacy, file_obj)

            self.assertEqual(load_postings(folder, "postings.json"), legacy)


if __name__ == "__main__":
    unittest.main()
