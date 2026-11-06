"""Command line entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .engine import apply_plan
from .models import Record, ValidationError
from .reconcile import build_sync_plan


def _load_records(path: Path) -> list[Record]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc

    if not isinstance(payload, list):
        raise ValidationError(f"{path} must contain a JSON array")
    return [Record.from_dict(item) for item in payload]


def _write_records(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reconcile versioned records without silently applying conflicts."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="apply creates and updates; conflicts remain untouched",
    )
    parser.add_argument("--output", type=Path, help="write updated target records")
    return parser


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    if args.output and not args.apply:
        parser.error("--output requires --apply")

    try:
        source = _load_records(args.source)
        target = _load_records(args.target)
        plan = build_sync_plan(source, target)
    except ValidationError as exc:
        parser.error(str(exc))

    summary: dict[str, Any] = plan.summary()

    if args.apply:
        result = apply_plan(target, plan)
        summary["events"] = [event.to_dict() for event in result.events]
        if args.output:
            _write_records(
                args.output,
                [record.to_dict() for record in result.records],
            )
            summary["output"] = str(args.output)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
