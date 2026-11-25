"""The universal collector: one config and constructed adapters in, data out.

Per adapter, run each declared step in order over one shared record set, honor
the config's step selection, record every step's outcome and merge the site
results by identity. No file writes, no spec checks, no site or profile import.
"""

from jobscraping.scrapers.steps import Step


def _step_pair(declared):
    if isinstance(declared, Step):
        return declared.name, declared.run
    return declared


def _step_report(name, status, records=None, error=None):
    return {"name": name, "status": status, "records": records, "error": error}


def _run_adapter(adapter, config):
    records = {}
    failed = False
    steps = []
    declared = [_step_pair(step) for step in adapter.steps]
    declared_names = {name for name, _ in declared}
    for name, run in declared:
        if config.steps and name not in config.steps:
            steps.append(_step_report(name, "skipped"))
            continue
        try:
            records = run(records, config)
        except Exception as error:  # noqa: BLE001 - adapters may raise anything
            failed = True
            steps.append(_step_report(name, "failed", error=str(error)))
            continue
        if not records:
            failed = True
            steps.append(_step_report(name, "empty", records=0))
            continue
        steps.append(_step_report(name, "ok", records=len(records)))
    for name in config.steps:
        if name not in declared_names:
            steps.append(_step_report(name, "skipped"))
    return {"source": adapter.source, "failed": failed, "steps": steps}, records


def run_collection(adapters, config):
    """Run every adapter's steps and return the merged records plus the report."""
    merged = {}
    sites = []
    for adapter in adapters:
        site, records = _run_adapter(adapter, config)
        sites.append(site)
        merged = {**merged, **records}
    zero_records = not merged
    report = {
        "scope_digest": config.scope_digest(),
        "sites": sites,
        "failed": zero_records or any(site["failed"] for site in sites),
        "zero_records": zero_records,
    }
    return {"records": merged, "report": report}
