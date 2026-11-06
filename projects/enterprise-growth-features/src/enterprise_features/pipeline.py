"""Train-scope-aware preprocessing with an auditable missing-value policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from .aggregation import ID_COLUMNS, build_feature_table
from .catalog import FEATURE_COLUMNS
from .config import FeatureConfig
from .models import DataQualityError, DatasetBundle


def _clean_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").replace(
        [np.inf, -np.inf], np.nan
    )


@dataclass(frozen=True)
class FeaturePipeline:
    medians: Mapping[str, float]

    @classmethod
    def fit(
        cls,
        raw_features: pd.DataFrame,
        train_ids: Iterable[str],
    ) -> "FeaturePipeline":
        ids = {str(value).strip() for value in train_ids if str(value).strip()}
        if not ids:
            raise DataQualityError("at least one training company id is required")

        available = set(raw_features["company_id"])
        unknown = sorted(ids - available)
        if unknown:
            raise DataQualityError(
                "training ids are not present in source data: "
                + ", ".join(unknown[:5])
            )

        training = raw_features.loc[raw_features["company_id"].isin(ids)]
        medians: dict[str, float] = {}
        for column in FEATURE_COLUMNS:
            value = _clean_numeric(training[column]).median()
            medians[column] = 0.0 if pd.isna(value) else float(value)
        return cls(medians=medians)

    def transform(self, raw_features: pd.DataFrame) -> pd.DataFrame:
        output = raw_features.loc[:, [*ID_COLUMNS, *FEATURE_COLUMNS]].copy()
        for column in FEATURE_COLUMNS:
            output[column] = _clean_numeric(output[column]).fillna(
                self.medians[column]
            )

        values = output.loc[:, FEATURE_COLUMNS].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise DataQualityError("feature preprocessing produced non-finite values")
        return output

    def to_dict(self) -> dict[str, Mapping[str, float]]:
        return {"training_medians": dict(self.medians)}


@dataclass(frozen=True)
class PipelineResult:
    features: pd.DataFrame
    raw_features: pd.DataFrame
    pipeline: FeaturePipeline
    report: Mapping[str, object]


def _rounded_missing_rates(raw_features: pd.DataFrame) -> dict[str, float]:
    return {
        column: round(float(raw_features[column].isna().mean()), 6)
        for column in FEATURE_COLUMNS
    }


def run_feature_pipeline(
    bundle: DatasetBundle,
    config: FeatureConfig,
    train_ids: Iterable[str],
) -> PipelineResult:
    ids = list(train_ids)
    raw_features = build_feature_table(bundle, config)
    pipeline = FeaturePipeline.fit(raw_features, ids)
    features = pipeline.transform(raw_features)

    report: dict[str, object] = {
        "as_of": bundle.as_of.date().isoformat(),
        "config_version": config.version,
        "recent_window_days": config.recent_window_days,
        "company_count": int(len(features)),
        "feature_count": len(FEATURE_COLUMNS),
        "training_company_count": len(set(ids)),
        "sources": {
            name: audit.to_dict() for name, audit in bundle.audit.items()
        },
        "missing_rate_before_imputation": _rounded_missing_rates(raw_features),
        "training_medians": {
            key: round(value, 8) for key, value in pipeline.medians.items()
        },
    }
    return PipelineResult(
        features=features,
        raw_features=raw_features,
        pipeline=pipeline,
        report=report,
    )
