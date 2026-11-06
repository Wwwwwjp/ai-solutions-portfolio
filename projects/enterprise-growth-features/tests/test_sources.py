from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from enterprise_features.models import DataQualityError
from enterprise_features.sources import EVENT_REQUIRED_COLUMNS, load_dataset


COMPANY_HEADER = [
    "company_id",
    "company_name",
    "sector",
    "province",
    "founded_at",
    "employees",
    "registered_capital_million_cny",
    "rd_staff_ratio",
    "revenue_million_cny",
]


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def write_minimal_dataset(
    root: Path,
    *,
    patent_rows: list[list[str]] | None = None,
    companies: list[list[str]] | None = None,
) -> None:
    write_csv(
        root / "companies.csv",
        COMPANY_HEADER,
        companies
        or [
            [
                "C-1",
                "Synthetic One",
                "software",
                "Jiangsu",
                "2015-01-01",
                "100",
                "50",
                "0.20",
                "80",
            ]
        ],
    )
    for name, columns in EVENT_REQUIRED_COLUMNS.items():
        rows = patent_rows if name == "patents" and patent_rows is not None else []
        write_csv(root / f"{name}.csv", sorted(columns), rows)


class SourceTests(unittest.TestCase):
    def test_future_events_are_excluded_and_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_dataset(
                root,
                patent_rows=[
                    ["C-1", "2024-01-01", "invention", "active"],
                    ["C-1", "2026-01-01", "invention", "pending"],
                ],
            )

            bundle = load_dataset(root, pd.Timestamp("2025-06-30"))

            self.assertEqual(len(bundle.events["patents"]), 1)
            self.assertEqual(bundle.audit["patents"].excluded_future_rows, 1)
            self.assertEqual(
                str(bundle.events["patents"].iloc[0]["event_date"].date()),
                "2024-01-01",
            )

    def test_duplicate_company_ids_are_rejected(self) -> None:
        duplicate = [
            "C-1",
            "Synthetic One",
            "software",
            "Jiangsu",
            "2015-01-01",
            "100",
            "50",
            "0.20",
            "80",
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_dataset(root, companies=[duplicate, duplicate])

            with self.assertRaisesRegex(DataQualityError, "duplicate company_id"):
                load_dataset(root, pd.Timestamp("2025-06-30"))

    def test_event_for_unknown_company_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_dataset(
                root,
                patent_rows=[
                    ["UNKNOWN", "2024-01-01", "invention", "active"],
                ],
            )

            with self.assertRaisesRegex(DataQualityError, "unknown company_id"):
                load_dataset(root, pd.Timestamp("2025-06-30"))


if __name__ == "__main__":
    unittest.main()
