"""Data specs: the contract a pipeline step's records satisfy.

A spec declares the fields processing relies on. Records stay dicts keyed by
identity; unknown fields are allowed and never removed.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldSpec:
    name: str
    kind: str                       # str | int | float | bool | date | list | dict | any
    required: bool = False
    produced_by: str | None = None  # step that fills it
    note: str = ""


@dataclass(frozen=True)
class DataSpec:
    name: str
    key: tuple[str, ...]
    fields: tuple[FieldSpec, ...]
    # ``key`` names the identity fields; the record dict key itself is chosen
    # by the caller and is not checked.

    def extend(self, *fields: FieldSpec) -> "DataSpec":
        """Return a spec with extra fields; the original is untouched."""
        return DataSpec(self.name, self.key, self.fields + fields)

    def check(self, records: dict[str, dict]) -> list[str]:
        """Report missing required fields; never mutate or coerce the records."""
        problems = []
        for record_id, record in records.items():
            for field in self.fields:
                if field.required and field.name not in record:
                    problems.append(f"{record_id}: missing required field '{field.name}'")
        return problems
