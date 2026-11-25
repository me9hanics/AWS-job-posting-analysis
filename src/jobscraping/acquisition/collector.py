"""The universal collector: one config and constructed adapters in, data out.

Per adapter, run each declared step in order over one shared record set, honor
the config's step selection, record every step's outcome and merge the site
results by identity. Writing chunks and the run report is opt-in through
``artifact_path``; no spec checks, no site module import.
"""

from jobscraping.acquisition.chunks import write_chunk, write_report
from jobscraping.scrapers.steps import Step


def _step_pair(declared):
    if isinstance(declared, Step):
        return declared.name, declared.run
    return declared


def _step_report(name, status, records=None, error=None):
    return {"name": name, "status": status, "records": records, "error": error}


def _declared_steps(adapter):
    """The adapter's steps, one per name, in declared order."""
    declared = []
    seen = set()
    for step in adapter.steps:
        name, run = _step_pair(step)
        if name not in seen:
            seen.add(name)
            declared.append((name, run))
    return declared


def _run_adapter(adapter, config, scope_digest, artifact_path=None):
    records = {}
    failed = False
    steps = []
    for name, run in _declared_steps(adapter):
        if config.steps and name not in config.steps:
            steps.append(_step_report(name, "skipped"))
            continue
        try:
            result = run(records, config)
        except Exception as error:
            failed = True
            steps.append(_step_report(name, "failed", error=str(error)))
            continue
        if not result:
            failed = True
            steps.append(_step_report(name, "empty", records=0))
            continue
        records = result
        steps.append(_step_report(name, "ok", records=len(records)))
        if artifact_path is not None:
            write_chunk(artifact_path, scope_digest, adapter.source, name, records)
    return {"source": adapter.source, "failed": failed, "steps": steps}, records


def failure_message(report) -> str:
    """Describe every failed or empty step, embedding its recorded error verbatim."""
    failures = []
    for site in report["sites"]:
        for step in site["steps"]:
            if step["status"] == "failed":
                failures.append(f"{site['source']} {step['name']}: {step['error']}")
            elif step["status"] == "empty":
                failures.append(f"{site['source']} {step['name']}: no records")
    if not failures:
        failures.append("no records collected")
    return "Collection failed: " + "; ".join(failures)


def run_collection(adapters, config, artifact_path=None):
    """Run every adapter's steps and return the merged records plus the report.

    With an ``artifact_path``, one chunk is written after each ``ok`` step and
    the run report once at the end, even for a failed run.
    """
    scope_digest = config.scope_digest()
    merged = {}
    sites = []
    for adapter in adapters:
        site, records = _run_adapter(adapter, config, scope_digest, artifact_path)
        sites.append(site)
        merged = {**merged, **records}
    zero_records = not merged
    report = {
        "scope_digest": scope_digest,
        "sites": sites,
        "failed": zero_records or any(site["failed"] for site in sites),
        "zero_records": zero_records,
    }
    if artifact_path is not None:
        write_report(artifact_path, report)
    return {"records": merged, "report": report}
