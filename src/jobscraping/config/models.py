"""The collection run's configuration: one object per YAML collection block."""

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field


def _digest_value(value):
    """Fallback for override values that JSON cannot serialize."""
    if isinstance(value, (set, frozenset)):
        return sorted(_digest_value(item) for item in value)
    return repr(value)


@dataclass(frozen=True)
class CollectionConfig:
    """One collection run: its scope, its step selection and its cache inputs."""

    sites: tuple[str, ...] = ()
    queries: tuple[str, ...] = ()
    locations: tuple[str, ...] = ()
    steps: tuple[str, ...] = ()
    overrides: Mapping[str, object] = field(default_factory=dict)
    cache_mode: str | None = None
    cached_postings: Mapping[str, dict] = field(default_factory=dict)
    cache_hit_predicate: Callable[[str, dict, dict | None], bool] | None = None

    def scope_digest(self) -> str:
        """A stable hash over the scope only; cache contents never change it."""
        scope = {
            "sites": list(self.sites),
            "queries": list(self.queries),
            "locations": list(self.locations),
            "steps": list(self.steps),
            "overrides": self.overrides,
        }
        payload = json.dumps(
            scope, sort_keys=True, separators=(",", ":"), default=_digest_value
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
