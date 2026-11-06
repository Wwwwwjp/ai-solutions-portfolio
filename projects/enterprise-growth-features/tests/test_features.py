from __future__ import annotations

from pathlib import Path
import unittest

import pandas as pd

from enterprise_features.aggregation import ID_COLUMNS, build_feature_table
from enterprise_features.catalog import FEATURE_COLUMNS
from enterprise_features.config import load_default_config
from enterprise_features.models import DataQualityError, DatasetBundle
from enterprise_features.pipeline import FeaturePipeline, run_feature_pipeline
from enterprise_features.sources import load_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "examples" / "data"


def empty_events() -> dict[str, pd.DataFrame]:
    return {
        "patents": pd.DataFrame(
            columns=["company_id", "event_date", "patent_type", "status"]
        ),
        "trademarks": pd.DataFrame(
            columns=["company_id", "event_date", "status"]
        ),
        "software_copyrights": pd.DataFrame(
            columns=["company_id", "event_date"]
        ),
        "platforms": pd.DataFrame(
            columns=["company_id", "event_date", "platform_type", "level"]
        ),
        "programs": pd.DataFrame(
            columns=[
                "company_id",
                "event_date",
                "program_type",
                "level",
                "award_amount_million_cny",
            ]
        ),
        "financings": pd.DataFrame(
            columns=[
                "company_id",
                "event_date",
                "round_type",
                "amount_million_cny",
                "investor_id",
            ]
        ),
        "talent": pd.DataFrame(
            columns=["company_id", "event_date", "talent_type", "level"]
        ),
    }


class FeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_default_config()

    def test_example_pipeline_matches_catalog_and_is_finite(self) -> None:
        bundle = load_dataset(DATA_DIR, pd.Timestamp("2025-06-30"))
        train_ids = (
            (DATA_DIR / "train_company_ids.txt")
            .read_text(encoding="utf-8")
            .splitlines()
        )

        result = run_feature_pipeline(bundle, self.config, train_ids)

        self.assertEqual(
            list(result.features.columns),
            [*ID_COLUMNS, *FEATURE_COLUMNS],
        )
        self.assertEqual(len(result.features), len(bundle.companies))
        self.assertFalse(result.features.isna().any().any())
        self.assertTrue(
            result.features.loc[:, FEATURE_COLUMNS]
            .apply(lambda column: column.map(lambda value: abs(value) < float("inf")))
            .all()
            .all()
        )
        self.assertGreater(
            sum(
                audit.excluded_future_rows
                for audit in bundle.audit.values()
            ),
            0,
        )

    def test_patent_weights_and_shares_are_applied(self) -> None:
        companies = pd.DataFrame(
            [
                {
                    "company_id": "C-1",
                    "company_name": "Synthetic One",
                    "sector": "software",
                    "province": "Jiangsu",
                    "founded_at": pd.Timestamp("2015-01-01"),
                    "employees": 100.0,
                    "registered_capital_million_cny": 50.0,
                    "rd_staff_ratio": 0.2,
                    "revenue_million_cny": 80.0,
                }
            ]
        )
        events = empty_events()
        events["patents"] = pd.DataFrame(
            [
                {
                    "company_id": "C-1",
                    "event_date": pd.Timestamp("2024-01-01"),
                    "patent_type": "invention",
                    "status": "active",
                },
                {
                    "company_id": "C-1",
                    "event_date": pd.Timestamp("2023-01-01"),
                    "patent_type": "utility_model",
                    "status": "expired",
                },
            ]
        )
        bundle = DatasetBundle(
            as_of=pd.Timestamp("2025-06-30"),
            companies=companies,
            events=events,
            audit={},
        )

        features = build_feature_table(bundle, self.config).iloc[0]

        self.assertEqual(features["patent_total"], 2.0)
        self.assertAlmostEqual(features["patent_weighted_score"], 3.0)
        self.assertAlmostEqual(features["patent_active_share"], 0.5)
        self.assertAlmostEqual(features["patent_invention_share"], 0.5)
        self.assertEqual(features["patent_type_diversity"], 2.0)

    def test_imputation_medians_use_training_ids_only(self) -> None:
        raw = pd.DataFrame(
            {
                "company_id": ["TRAIN", "EVAL"],
                "company_name": ["Train", "Eval"],
                "sector": ["software", "software"],
                "province": ["Jiangsu", "Jiangsu"],
            }
        )
        for column in FEATURE_COLUMNS:
            raw[column] = 1.0
        raw.loc[0, "rd_staff_ratio"] = 0.10
        raw.loc[1, "rd_staff_ratio"] = float("nan")

        pipeline = FeaturePipeline.fit(raw, ["TRAIN"])
        transformed = pipeline.transform(raw)

        self.assertAlmostEqual(pipeline.medians["rd_staff_ratio"], 0.10)
        self.assertAlmostEqual(transformed.loc[1, "rd_staff_ratio"], 0.10)
        self.assertFalse(transformed.isna().any().any())

    def test_unknown_category_is_rejected(self) -> None:
        companies = pd.DataFrame(
            [
                {
                    "company_id": "C-1",
                    "company_name": "Synthetic One",
                    "sector": "software",
                    "province": "Jiangsu",
                    "founded_at": pd.Timestamp("2015-01-01"),
                    "employees": 100.0,
                    "registered_capital_million_cny": 50.0,
                    "rd_staff_ratio": 0.2,
                    "revenue_million_cny": 80.0,
                }
            ]
        )
        events = empty_events()
        events["patents"] = pd.DataFrame(
            [
                {
                    "company_id": "C-1",
                    "event_date": pd.Timestamp("2024-01-01"),
                    "patent_type": "unmapped_type",
                    "status": "active",
                }
            ]
        )
        bundle = DatasetBundle(
            as_of=pd.Timestamp("2025-06-30"),
            companies=companies,
            events=events,
            audit={},
        )

        with self.assertRaisesRegex(DataQualityError, "unmapped values"):
            build_feature_table(bundle, self.config)

    def test_no_event_families_use_zero_not_median_counts(self) -> None:
        companies = pd.DataFrame(
            [
                {
                    "company_id": "C-1",
                    "company_name": "Synthetic One",
                    "sector": "software",
                    "province": "Jiangsu",
                    "founded_at": pd.Timestamp("2015-01-01"),
                    "employees": 100.0,
                    "registered_capital_million_cny": 50.0,
                    "rd_staff_ratio": 0.2,
                    "revenue_million_cny": 80.0,
                }
            ]
        )
        bundle = DatasetBundle(
            as_of=pd.Timestamp("2025-06-30"),
            companies=companies,
            events=empty_events(),
            audit={},
        )

        features = build_feature_table(bundle, self.config).iloc[0]

        for column in (
            "patent_total",
            "patent_frequency_per_year",
            "trademark_total",
            "platform_total",
            "program_total",
            "program_award_million_cny_log",
            "financing_total",
            "financing_amount_million_cny_log",
            "investor_count",
            "talent_total",
            "recent_activity_families",
        ):
            self.assertEqual(features[column], 0.0, column)


if __name__ == "__main__":
    unittest.main()
