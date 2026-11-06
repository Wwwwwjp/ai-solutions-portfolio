from __future__ import annotations

import unittest

from workflow_reliability.engine import Action, apply_plan
from workflow_reliability.models import Record, ValidationError
from workflow_reliability.reconcile import build_sync_plan


def record(key: str, version: int, fields: dict[str, object]) -> Record:
    return Record(
        key=key,
        version=version,
        fields=fields,
        updated_at="2026-01-01T00:00:00+00:00",
    )


class EngineTests(unittest.TestCase):
    def test_apply_is_idempotent(self) -> None:
        source = [
            record("new", 1, {"status": "open"}),
            record("update", 2, {"status": "closed"}),
        ]
        target = [record("update", 1, {"status": "open"})]

        first_plan = build_sync_plan(source, target)
        first_result = apply_plan(target, first_plan)
        self.assertTrue(first_plan.has_changes)

        second_plan = build_sync_plan(source, first_result.records)
        self.assertFalse(second_plan.has_changes)
        self.assertEqual(len(second_plan.unchanged), 2)

    def test_conflicts_and_orphans_are_not_applied(self) -> None:
        source = [record("conflict", 1, {"owner": "source"})]
        target = [
            record("conflict", 1, {"owner": "target"}),
            record("orphan", 3, {"status": "open"}),
        ]

        plan = build_sync_plan(source, target)
        result = apply_plan(target, plan)

        self.assertEqual(result.records, tuple(sorted(target, key=lambda item: item.key)))
        actions = [event.action for event in result.events]
        self.assertEqual(actions, [Action.CONFLICT, Action.ORPHANED])

    def test_events_include_conflict_reason(self) -> None:
        source = [record("conflict", 1, {"owner": "source"})]
        target = [record("conflict", 2, {"owner": "target"})]

        result = apply_plan(target, build_sync_plan(source, target))

        self.assertEqual(result.events[0].reason, "target_ahead")

    def test_duplicate_target_keys_are_rejected_during_apply(self) -> None:
        target = [
            record("duplicate", 1, {"status": "open"}),
            record("duplicate", 2, {"status": "closed"}),
        ]
        empty_plan = build_sync_plan([], [])

        with self.assertRaisesRegex(ValidationError, "duplicate target record key"):
            apply_plan(target, empty_plan)


if __name__ == "__main__":
    unittest.main()
