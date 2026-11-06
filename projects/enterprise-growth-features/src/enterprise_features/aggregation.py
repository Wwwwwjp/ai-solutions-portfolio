"""Point-in-time event aggregation and business feature construction."""

from __future__ import annotations

from datetime import timedelta
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from .catalog import FEATURE_COLUMNS
from .config import FeatureConfig
from .models import DataQualityError, DatasetBundle


ID_COLUMNS = ("company_id", "company_name", "sector", "province")


def _empty_timing(prefix: str) -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            f"{prefix}_total",
            f"{prefix}_recent_share",
            f"{prefix}_recency_days",
        ]
    )


def _validate_keys(
    values: pd.Series,
    weights: Mapping[str, float],
    source: str,
    column: str,
) -> None:
    unknown = sorted(set(values.dropna()) - set(weights))
    if unknown:
        raise DataQualityError(
            f"{source}.{column} contains unmapped values: {', '.join(unknown)}"
        )


def _timing_features(
    events: pd.DataFrame,
    as_of: pd.Timestamp,
    prefix: str,
    recent_window_days: int,
    *,
    include_frequency: bool = False,
) -> pd.DataFrame:
    if events.empty:
        result = _empty_timing(prefix)
        if include_frequency:
            result[f"{prefix}_frequency_per_year"] = pd.Series(dtype=float)
        return result

    grouped = events.groupby("company_id", sort=True)
    result = grouped["event_date"].agg(
        total="size",
        latest="max",
        earliest="min",
    )
    recent_start = as_of - timedelta(days=recent_window_days)
    recent_counts = (
        events.loc[events["event_date"] >= recent_start]
        .groupby("company_id", sort=True)
        .size()
    )
    result["recent_count"] = recent_counts.reindex(result.index, fill_value=0)
    result[f"{prefix}_total"] = result["total"].astype(float)
    result[f"{prefix}_recent_share"] = (
        result["recent_count"] / result["total"]
    ).fillna(0.0)
    result[f"{prefix}_recency_days"] = (
        as_of - result["latest"]
    ).dt.total_seconds() / 86_400
    if include_frequency:
        span_years = (
            (result["latest"] - result["earliest"]).dt.total_seconds()
            / 86_400
            / 365.25
        )
        result[f"{prefix}_frequency_per_year"] = result["total"] / span_years.clip(
            lower=1.0
        )
    return result.drop(columns=["total", "latest", "earliest", "recent_count"])


def _patent_features(
    events: pd.DataFrame,
    as_of: pd.Timestamp,
    config: FeatureConfig,
) -> pd.DataFrame:
    result = _timing_features(
        events,
        as_of,
        "patent",
        config.recent_window_days,
        include_frequency=True,
    )
    if events.empty:
        for column in (
            "patent_weighted_score",
            "patent_active_share",
            "patent_invention_share",
            "patent_type_diversity",
        ):
            result[column] = pd.Series(dtype=float)
        return result

    _validate_keys(
        events["patent_type"],
        config.patent_type_weights,
        "patents",
        "patent_type",
    )
    _validate_keys(
        events["status"],
        config.patent_status_weights,
        "patents",
        "status",
    )

    weighted = events.copy()
    weighted["type_weight"] = weighted["patent_type"].map(
        config.patent_type_weights
    )
    weighted["status_weight"] = weighted["status"].map(
        config.patent_status_weights
    )
    weighted["patent_weight"] = (
        weighted["type_weight"] * weighted["status_weight"]
    )
    grouped = weighted.groupby("company_id", sort=True)

    result["patent_weighted_score"] = grouped["patent_weight"].sum()
    result["patent_active_share"] = grouped["status"].apply(
        lambda values: float((values == "active").mean())
    )
    result["patent_invention_share"] = grouped["patent_type"].apply(
        lambda values: float((values == "invention").mean())
    )
    result["patent_type_diversity"] = grouped["patent_type"].nunique()
    return result


def _categorical_timing_features(
    events: pd.DataFrame,
    as_of: pd.Timestamp,
    prefix: str,
    recent_window_days: int,
) -> pd.DataFrame:
    return _timing_features(
        events,
        as_of,
        prefix,
        recent_window_days,
    )


def _platform_features(
    events: pd.DataFrame,
    as_of: pd.Timestamp,
    config: FeatureConfig,
) -> pd.DataFrame:
    result = _categorical_timing_features(
        events,
        as_of,
        "platform",
        config.recent_window_days,
    )
    if events.empty:
        for column in (
            "platform_weighted_score",
            "national_platform_count",
            "platform_type_diversity",
        ):
            result[column] = pd.Series(dtype=float)
        return result

    _validate_keys(
        events["level"],
        config.platform_level_weights,
        "platforms",
        "level",
    )
    weighted = events.copy()
    weighted["level_weight"] = weighted["level"].map(
        config.platform_level_weights
    )
    grouped = weighted.groupby("company_id", sort=True)
    result["platform_weighted_score"] = grouped["level_weight"].sum()
    result["national_platform_count"] = grouped["level"].apply(
        lambda values: float((values == "national").sum())
    )
    result["platform_type_diversity"] = grouped["platform_type"].nunique()
    return result


def _program_features(
    events: pd.DataFrame,
    as_of: pd.Timestamp,
    config: FeatureConfig,
) -> pd.DataFrame:
    result = _categorical_timing_features(
        events,
        as_of,
        "program",
        config.recent_window_days,
    )
    if events.empty:
        for column in (
            "program_award_million_cny",
            "program_award_million_cny_log",
            "program_weighted_score",
            "program_level_diversity",
        ):
            result[column] = pd.Series(dtype=float)
        return result

    _validate_keys(
        events["level"],
        config.program_level_weights,
        "programs",
        "level",
    )
    weighted = events.copy()
    weighted["level_weight"] = weighted["level"].map(
        config.program_level_weights
    )
    grouped = weighted.groupby("company_id", sort=True)
    award = grouped["award_amount_million_cny"].sum(min_count=1).fillna(0.0)
    result["program_award_million_cny"] = award
    result["program_award_million_cny_log"] = np.log1p(award)
    result["program_weighted_score"] = grouped["level_weight"].sum()
    result["program_level_diversity"] = grouped["level"].nunique()
    return result


def _financing_features(
    events: pd.DataFrame,
    as_of: pd.Timestamp,
    config: FeatureConfig,
) -> pd.DataFrame:
    result = _categorical_timing_features(
        events,
        as_of,
        "financing",
        config.recent_window_days,
    )
    if events.empty:
        for column in (
            "financing_amount_million_cny",
            "financing_amount_million_cny_log",
            "financing_weighted_score",
            "investor_count",
        ):
            result[column] = pd.Series(dtype=float)
        return result

    _validate_keys(
        events["round_type"],
        config.financing_round_weights,
        "financings",
        "round_type",
    )
    weighted = events.copy()
    weighted["round_weight"] = weighted["round_type"].map(
        config.financing_round_weights
    )
    grouped = weighted.groupby("company_id", sort=True)
    amount = grouped["amount_million_cny"].sum(min_count=1).fillna(0.0)
    result["financing_amount_million_cny"] = amount
    result["financing_amount_million_cny_log"] = np.log1p(amount)
    result["financing_weighted_score"] = grouped["round_weight"].sum()
    result["investor_count"] = grouped["investor_id"].nunique()
    return result


def _talent_features(
    events: pd.DataFrame,
    as_of: pd.Timestamp,
    config: FeatureConfig,
) -> pd.DataFrame:
    result = _categorical_timing_features(
        events,
        as_of,
        "talent",
        config.recent_window_days,
    )
    if events.empty:
        for column in (
            "talent_weighted_score",
            "national_talent_share",
        ):
            result[column] = pd.Series(dtype=float)
        return result

    _validate_keys(
        events["level"],
        config.talent_level_weights,
        "talent",
        "level",
    )
    weighted = events.copy()
    weighted["level_weight"] = weighted["level"].map(
        config.talent_level_weights
    )
    grouped = weighted.groupby("company_id", sort=True)
    result["talent_weighted_score"] = grouped["level_weight"].sum()
    result["national_talent_share"] = grouped["level"].apply(
        lambda values: float((values == "national").mean())
    )
    return result


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    result = numerator / denominator.replace(0, np.nan)
    return result.replace([np.inf, -np.inf], np.nan)


def build_feature_table(
    bundle: DatasetBundle,
    config: FeatureConfig,
) -> pd.DataFrame:
    """Build raw features using only records visible at the cutoff."""
    base = bundle.companies.copy()
    base["company_age_years"] = (
        (bundle.as_of - base["founded_at"]).dt.days / 365.25
    )
    base["employees_log"] = np.log1p(base["employees"])
    base["registered_capital_log"] = np.log1p(
        base["registered_capital_million_cny"]
    )
    base["rd_staff_ratio_missing"] = (
        base["rd_staff_ratio"].isna().astype(int)
    )
    base["revenue_million_cny_log"] = np.log1p(
        base["revenue_million_cny"]
    )

    features = base.set_index("company_id")
    aggregates: Iterable[pd.DataFrame] = (
        _patent_features(bundle.events["patents"], bundle.as_of, config),
        _categorical_timing_features(
            bundle.events["trademarks"],
            bundle.as_of,
            "trademark",
            config.recent_window_days,
        ),
        _categorical_timing_features(
            bundle.events["software_copyrights"],
            bundle.as_of,
            "software_copyright",
            config.recent_window_days,
        ),
        _platform_features(bundle.events["platforms"], bundle.as_of, config),
        _program_features(bundle.events["programs"], bundle.as_of, config),
        _financing_features(bundle.events["financings"], bundle.as_of, config),
        _talent_features(bundle.events["talent"], bundle.as_of, config),
    )
    for aggregate in aggregates:
        features = features.join(aggregate, how="left")

    available_features = [
        column for column in FEATURE_COLUMNS if column in features.columns
    ]
    features.loc[:, available_features] = features.loc[
        :, available_features
    ].apply(pd.to_numeric, errors="coerce")
    zero_fill_columns = [
        column
        for column in FEATURE_COLUMNS
        if any(
            column == f"{prefix}_total"
            or column.startswith(f"{prefix}_")
            for prefix in (
                "patent",
                "trademark",
                "software_copyright",
                "platform",
                "program",
                "financing",
                "talent",
            )
        )
        and column.endswith(
            (
                "_total",
                "_share",
                "_score",
                "_diversity",
                "_count",
            )
        )
    ]
    zero_fill_columns.extend(
        [
            "national_platform_count",
            "investor_count",
            "patent_frequency_per_year",
        ]
    )
    zero_fill_columns = sorted(set(zero_fill_columns))
    features[zero_fill_columns] = (
        features[zero_fill_columns]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
    )

    features["program_award_million_cny"] = features[
        "program_award_million_cny"
    ].fillna(0.0)
    features["financing_amount_million_cny"] = features[
        "financing_amount_million_cny"
    ].fillna(0.0)
    features["patent_frequency_per_year"] = features[
        "patent_frequency_per_year"
    ].fillna(0.0)
    features["program_award_million_cny_log"] = np.log1p(
        features["program_award_million_cny"]
    )
    features["financing_amount_million_cny_log"] = np.log1p(
        features["financing_amount_million_cny"]
    )

    features["recent_activity_families"] = (
        features[
            [
                "patent_recent_share",
                "trademark_recent_share",
                "software_copyright_recent_share",
                "platform_recent_share",
                "program_recent_share",
                "financing_recent_share",
                "talent_recent_share",
            ]
        ]
        .gt(0)
        .sum(axis=1)
        .astype(float)
    )
    features["ip_per_100_employees"] = _safe_ratio(
        features["patent_total"] + features["software_copyright_total"],
        features["employees"] / 100.0,
    )
    features["research_platform_per_1000_employees"] = _safe_ratio(
        features["platform_total"],
        features["employees"] / 1_000.0,
    )
    features["external_support_to_revenue_ratio"] = _safe_ratio(
        features["program_award_million_cny"],
        features["revenue_million_cny"],
    )
    features["funding_to_revenue_ratio"] = _safe_ratio(
        features["financing_amount_million_cny"],
        features["revenue_million_cny"],
    )
    features.loc[:, FEATURE_COLUMNS] = features.loc[
        :, FEATURE_COLUMNS
    ].apply(pd.to_numeric, errors="coerce")

    features = features.reset_index()
    missing = sorted(set(FEATURE_COLUMNS) - set(features.columns))
    if missing:
        raise DataQualityError(
            "feature catalog is not aligned with output: " + ", ".join(missing)
        )
    return features.loc[:, [*ID_COLUMNS, *FEATURE_COLUMNS]]
