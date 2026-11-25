"""Source-level quality gate run after collecting and before storing."""


def validate_postings_quality(
    postings,
    previous_postings=None,
    required_fields_by_source=None,
    minimum_source_retention=None,
    minimum_field_completeness_by_source=None,
    verbose=False,
):
    """Raise before saving when configured source-level quality checks fail."""
    previous_postings = previous_postings or {}
    required_fields_by_source = required_fields_by_source or {}
    minimum_source_retention = minimum_source_retention or {}
    minimum_field_completeness_by_source = minimum_field_completeness_by_source or {}
    sources = (set(required_fields_by_source) | set(minimum_source_retention)
               | set(minimum_field_completeness_by_source))
    reports = []
    failures = []

    for source in sorted(sources):
        source_postings = [
            posting
            for posting in postings.values()
            if posting.get("source") == source
        ]
        field_counts = {
            field: sum(not posting.get(field) for posting in source_postings)
            for field in required_fields_by_source.get(source, ())
        }
        field_report = ", ".join(
            f"{field}={count}" for field, count in field_counts.items()
        )
        if field_report:
            reports.append(f"{source}: {field_report}")
        failed_fields = {
            field: count
            for field, count in field_counts.items()
            if count and (
                field not in minimum_field_completeness_by_source.get(source, {})
                or (len(source_postings) - count) / len(source_postings)
                < minimum_field_completeness_by_source[source][field]
            )
        }
        if failed_fields:
            failures.append(f"{source}: {field_report}")

        minimum_retention = minimum_source_retention.get(source)
        if minimum_retention is not None:
            previous_count = sum(
                posting.get("source") == source
                for posting in previous_postings.values()
            )
            current_count = len(source_postings)
            if previous_count:
                retention = current_count / previous_count
                retention_report = (
                    f"{source}: retained {current_count}/{previous_count} "
                    f"({retention:.1%})"
                )
                reports.append(retention_report)
                if retention < minimum_retention:
                    failures.append(retention_report)

    if verbose and reports:
        print("Posting quality: " + "; ".join(reports))
    if failures:
        raise ValueError(
            "Posting quality gate failed; no output files were written: "
            + "; ".join(failures)
        )
