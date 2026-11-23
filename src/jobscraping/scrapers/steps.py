"""The adapter step contract: named operations on one shared record set.

A step list may also be plain ``(name, callable)`` pairs; ``Step`` is a
convenience for adapters that want to declare their specs, not a framework.
There are no required/optional flags and no registry or validation hierarchy:
the collector calls each callable with ``(records, config)`` and rebinds the
result. An empty step selection means every declared step runs.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

from jobscraping.specs.base import DataSpec


RecordSet = dict[str, dict]


class CollectionConfigLike(Protocol):
    """The part of the collection config a step may read.

    The concrete ``CollectionConfig`` lands with B32; until then a step is
    configured by anything that carries these values.
    """

    sites: tuple[str, ...]
    queries: tuple[str, ...]
    locations: tuple[str, ...]
    steps: tuple[str, ...]
    overrides: Mapping[str, object]
    cache_mode: str | None


StepRun = Callable[[RecordSet, CollectionConfigLike], RecordSet]


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
