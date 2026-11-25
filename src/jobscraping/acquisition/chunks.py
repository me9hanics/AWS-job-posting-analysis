"""Chunk and run-report artifacts for the collector.

One chunk per completed step under ``chunks/<scope-digest>/<source>/<step>.json``
and one ``run_report.json`` per run of a scope. Until B30 supplies the atomic
write, ``files_io.save_data`` is the writer.
"""

from pathlib import Path

from jobscraping.io.files_io import save_data


def chunk_path(path, scope_digest, source, step) -> Path:
    """The file a step's chunk is written to for one scope and source."""
    return Path(path) / "chunks" / scope_digest / source / f"{step}.json"


def write_chunk(path, scope_digest, source, step, records) -> Path:
    """Write one step's records and return the file path."""
    target = chunk_path(path, scope_digest, source, step)
    content = {"source": source, "step": step, "records": records}
    save_data(content, path=f"{target.parent}/", name=target.name, with_timestamp=False)
    return target


def write_report(path, report) -> Path:
    """Write the run report under ``path`` and return the file path."""
    target = Path(path) / "run_report.json"
    save_data(report, path=f"{Path(path)}/", name=target.name, with_timestamp=False)
    return target
