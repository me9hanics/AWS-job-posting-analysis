"""The adapter step contract: named operations on one shared record set.

A step list may also be plain ``(name, callable)`` pairs; ``Step`` is a
convenience for adapters that want to declare their specs, not a framework.
There are no required/optional flags and no registry or validation hierarchy:
the collector calls each callable with ``(records, config)`` and rebinds the
result.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from jobscraping.specs.base import DataSpec


RecordSet = dict[str, dict]
StepRun = Callable[[RecordSet, Any], RecordSet]  # config type arrives in B32


@dataclass(frozen=True)
class Step:
    name: str
    run: StepRun
    input_spec: DataSpec | None = None
    output_spec: DataSpec | None = None


class SiteAdapter(Protocol):
    """One source: its name and its ordered steps."""

    source: str
    steps: tuple[Step | tuple[str, StepRun], ...]
