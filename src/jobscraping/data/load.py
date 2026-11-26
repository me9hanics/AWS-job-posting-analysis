"""Load and persist posting records at relative vault paths."""

from datetime import UTC, datetime
from pathlib import Path

from jobscraping.config.constants import SCHEMA_VERSION, VAULT_META_FILENAME
from jobscraping.io.files_io import load_file_if_str, save_data


def load_postings(path, filename):
    file = Path(path) / filename
    return load_file_if_str(str(file), "dict") if file.exists() else {}


def save_json(data, path, filename, *, with_timestamp: bool = False) -> Path:
    """Write one JSON artifact through the format layer; return its path."""
    return save_data(data, path=str(path) + "/", name=filename,
                     with_timestamp=with_timestamp)


def save_vault_meta(path, updated_at=None) -> Path:
    """Write the vault's schema marker; return its path."""
    if updated_at is None:
        updated_at = datetime.now(UTC).isoformat()
    return save_json({"schema_version": SCHEMA_VERSION, "updated_at": updated_at},
                     path, VAULT_META_FILENAME)


def load_vault_meta(path) -> dict:
    """Return the vault's schema marker, or {} when the vault has none."""
    return load_postings(path, VAULT_META_FILENAME)


def save_posting_set(records, path, filename) -> Path:
    """Write a posting set plus the vault meta; return the posting file's path."""
    target = save_json(records, path, filename)
    save_vault_meta(path)
    return target
