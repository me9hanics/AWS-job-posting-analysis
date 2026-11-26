"""Neutral identity diff between two posting record mappings."""


def get_added_and_removed(new: dict, previous: dict) -> tuple[dict, dict]:
    """Return (added, removed) as an identity-set difference over record keys.

    Records are returned by reference in the input's insertion order; neither
    input is mutated, enriched, or ordered by any field.
    """
    added = {key: record for key, record in new.items() if key not in previous}
    removed = {key: record for key, record in previous.items() if key not in new}
    return added, removed
