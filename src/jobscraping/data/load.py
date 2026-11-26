"""Load and persist posting records at relative vault paths."""

from pathlib import Path

from jobscraping.io.files_io import load_file_if_str, save_data, save_list


def load_postings(path, filename):
    file = Path(path) / filename
    return load_file_if_str(str(file), "dict") if file.exists() else {}


def save_json(data, path, filename, *, with_timestamp: bool = False) -> Path:
    """Write one JSON artifact through the format layer; return its path."""
    return save_data(data, path=str(path) + "/", name=filename,
                     with_timestamp=with_timestamp)


def save_posting_set(records, path, filename) -> Path:
    """Write a posting set as one JSON artifact; return its path."""
    target = Path(path) / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(records, list):
        save_list(records, filename=str(target))
        return target
    return save_json(records, path, filename)
