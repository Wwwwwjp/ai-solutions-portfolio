from __future__ import annotations

import unittest

from workflow_reliability.models import Record, ValidationError
from workflow_reliability.reconcile import build_sync_plan


def record(
    key: str,
    version: int,
    fields: dict[str, object],
    updated_at: str = "2026-01-01T00:00:00+00:00",
) -> Record:
    return Record(key=key, version=version, fields=fields, updated_at=updated_at)


class ReconcileTests(unittest.TestCase):
    def test_classifies_all_outcomes(self) -> None:
        source = [
            record("new", 1, {"status": "open"}),
            record("newer", 2, {"status": "open"}),
            record("same", 1, {"status": "done"}),
            record("diverged", 1, {"owner": "source"}),
            record("stale", 1, {"status": "open"}),
        ]
        target = [
            record("newer", 1, {"status": "assigned"}),
            record("same", 1, {"status": "done"}),
            record("diverged", 1, {"owner": "target"}),
            record("stale", 2, {"status": "closed"}),
            record("orphaned", 4, {"status": "open"}),
        ]

        plan = build_sync_plan(source, target)

        self.assertEqual([item.key for item in plan.creates], ["new"])
        self.assertEqual([item.key for item in plan.updates], ["newer"])
        self.assertEqual([item.key for item in plan.unchanged], ["same"])
        self.assertEqual([item.key for item in plan.conflicts], ["diverged", "stale"])
        self.assertEqual([item.key for item in plan.orphaned], ["orphaned"])

    def test_duplicate_keys_are_rejected(self) -> None:
        source = [
            record("same-key", 1, {"status": "open"}),
            record("same-key", 2, {"status": "closed"}),
        ]
        with self.assertRaisesRegex(ValidationError, "duplicate source record key"):
            build_sync_plan(source, [])

    def test_invalid_version_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "non-negative integer"):
            Record.from_dict(
                {
                    "key": "A-1",
                    "version": -1,
                    "fields": {},
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            )

    def test_same_version_comparison_ignores_timestamp(self) -> None:
        source = [record("A-1", 1, {"status": "open"}, "2026-01-01T00:00:00+00:00")]
        target = [record("A-1", 1, {"status": "open"}, "2026-01-02T00:00:00+00:00")]
        plan = build_sync_plan(source, target)
        self.assertEqual(len(plan.unchanged), 1)
        self.assertEqual(len(plan.conflicts), 0)


if __name__ == "__main__":
    unittest.main()
