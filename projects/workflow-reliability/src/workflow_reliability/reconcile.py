"""Pure reconciliation logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Record, ValidationError


@dataclass(frozen=True)
class Conflict:
    key: str
    reason: str
    source: Record
    target: Record

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "reason": self.reason,
            "source_version": self.source.version,
            "target_version": self.target.version,
        }


@dataclass(frozen=True)
class SyncPlan:
    creates: tuple[Record, ...]
    updates: tuple[Record, ...]
    unchanged: tuple[Record, ...]
    conflicts: tuple[Conflict, ...]
    orphaned: tuple[Record, ...]

    @property
    def has_changes(self) -> bool:
        return bool(self.creates or self.updates)

    def summary(self) -> dict[str, int]:
        return {
            "conflicts": len(self.conflicts),
            "creates": len(self.creates),
            "orphaned": len(self.orphaned),
            "unchanged": len(self.unchanged),
            "updates": len(self.updates),
        }


def _index(records: Iterable[Record], side: str) -> dict[str, Record]:
    indexed: dict[str, Record] = {}
    for record in records:
        if record.key in indexed:
            raise ValidationError(f"duplicate {side} record key: {record.key}")
        indexed[record.key] = record
    return indexed


def build_sync_plan(
    source_records: Iterable[Record],
    target_records: Iterable[Record],
) -> SyncPlan:
    """Classify source and target records without mutating either side."""
    source = _index(source_records, "source")
    target = _index(target_records, "target")

    creates: list[Record] = []
    updates: list[Record] = []
    unchanged: list[Record] = []
    conflicts: list[Conflict] = []

    for key, source_record in source.items():
        target_record = target.get(key)
        if target_record is None:
            creates.append(source_record)
            continue

        if source_record.version > target_record.version:
            updates.append(source_record)
        elif source_record.version < target_record.version:
            conflicts.append(
                Conflict(
                    key=key,
                    reason="target_ahead",
                    source=source_record,
                    target=target_record,
                )
            )
        elif source_record.fingerprint != target_record.fingerprint:
            conflicts.append(
                Conflict(
                    key=key,
                    reason="same_version_divergence",
                    source=source_record,
                    target=target_record,
                )
            )
        else:
            unchanged.append(source_record)

    orphaned = tuple(
        record for key, record in target.items() if key not in source
    )

    return SyncPlan(
        creates=tuple(creates),
        updates=tuple(updates),
        unchanged=tuple(unchanged),
        conflicts=tuple(conflicts),
        orphaned=orphaned,
    )
