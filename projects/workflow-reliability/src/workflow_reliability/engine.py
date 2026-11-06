"""Plan application and audit event generation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .models import Record, ValidationError
from .reconcile import Conflict, SyncPlan


class Action(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    CONFLICT = "conflict"
    ORPHANED = "orphaned"


@dataclass(frozen=True)
class SyncEvent:
    action: Action
    key: str
    version: int
    reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "action": self.action.value,
            "key": self.key,
            "version": self.version,
        }
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


@dataclass(frozen=True)
class ApplyResult:
    records: tuple[Record, ...]
    events: tuple[SyncEvent, ...]
    conflicts: tuple[Conflict, ...]


def apply_plan(
    current_target: Iterable[Record],
    plan: SyncPlan,
) -> ApplyResult:
    """Apply creates and updates, leaving conflicts and orphans untouched."""
    merged: dict[str, Record] = {}
    for record in current_target:
        if record.key in merged:
            raise ValidationError(f"duplicate target record key: {record.key}")
        merged[record.key] = record

    events: list[SyncEvent] = []

    for record in plan.creates:
        merged[record.key] = record
        events.append(SyncEvent(Action.CREATE, record.key, record.version))

    for record in plan.updates:
        merged[record.key] = record
        events.append(SyncEvent(Action.UPDATE, record.key, record.version))

    for conflict in plan.conflicts:
        events.append(
            SyncEvent(
                Action.CONFLICT,
                conflict.key,
                conflict.source.version,
                reason=conflict.reason,
            )
        )

    for record in plan.orphaned:
        events.append(
            SyncEvent(
                Action.ORPHANED,
                record.key,
                record.version,
                reason="source_record_missing",
            )
        )

    return ApplyResult(
        records=tuple(merged[key] for key in sorted(merged)),
        events=tuple(events),
        conflicts=plan.conflicts,
    )
