"""Human-readable definitions for every generated feature."""

from __future__ import annotations

import pandas as pd

from .models import FeatureDefinition


def _feature(
    name: str,
    family: str,
    description: str,
    missing_policy: str,
) -> FeatureDefinition:
    return FeatureDefinition(name, family, description, missing_policy)


FEATURE_DEFINITIONS: tuple[FeatureDefinition, ...] = (
    _feature(
        "company_age_years",
        "company",
        "Years between founding date and the point-in-time cutoff.",
        "direct",
    ),
    _feature(
        "employees_log",
        "company",
        "Natural log of one plus employee count.",
        "median_from_training",
    ),
    _feature(
        "registered_capital_log",
        "company",
        "Natural log of one plus registered capital in millions of CNY.",
        "median_from_training",
    ),
    _feature(
        "rd_staff_ratio",
        "company",
        "Share of employees assigned to research and development.",
        "median_from_training",
    ),
    _feature(
        "rd_staff_ratio_missing",
        "data_quality",
        "Indicator for a missing R&D staffing ratio in the source data.",
        "zero_when_not_missing",
    ),
    _feature(
        "revenue_million_cny_log",
        "company",
        "Natural log of one plus revenue in millions of CNY.",
        "median_from_training",
    ),
    _feature(
        "patent_total",
        "intellectual_property",
        "Number of patent records on or before the cutoff.",
        "zero_when_no_event",
    ),
    _feature(
        "patent_weighted_score",
        "intellectual_property",
        "Patent count weighted by configured patent type and status weights.",
        "zero_when_no_event",
    ),
    _feature(
        "patent_active_share",
        "intellectual_property",
        "Share of patents with active status.",
        "zero_when_no_event",
    ),
    _feature(
        "patent_invention_share",
        "intellectual_property",
        "Share of patents classified as inventions.",
        "zero_when_no_event",
    ),
    _feature(
        "patent_type_diversity",
        "intellectual_property",
        "Number of distinct patent types.",
        "zero_when_no_event",
    ),
    _feature(
        "patent_recent_share",
        "intellectual_property",
        "Share of patents filed inside the configured recent window.",
        "zero_when_no_event",
    ),
    _feature(
        "patent_recency_days",
        "intellectual_property",
        "Days from the latest patent to the cutoff.",
        "median_from_training",
    ),
    _feature(
        "patent_frequency_per_year",
        "intellectual_property",
        "Patent count divided by active filing span, with a one-year floor.",
        "zero_when_no_event",
    ),
    _feature(
        "trademark_total",
        "intellectual_property",
        "Number of trademark records on or before the cutoff.",
        "zero_when_no_event",
    ),
    _feature(
        "trademark_recent_share",
        "intellectual_property",
        "Share of trademarks filed inside the configured recent window.",
        "zero_when_no_event",
    ),
    _feature(
        "trademark_recency_days",
        "intellectual_property",
        "Days from the latest trademark to the cutoff.",
        "median_from_training",
    ),
    _feature(
        "software_copyright_total",
        "intellectual_property",
        "Number of software copyright registrations.",
        "zero_when_no_event",
    ),
    _feature(
        "software_copyright_recent_share",
        "intellectual_property",
        "Share of software registrations inside the recent window.",
        "zero_when_no_event",
    ),
    _feature(
        "software_copyright_recency_days",
        "intellectual_property",
        "Days from the latest software registration to the cutoff.",
        "median_from_training",
    ),
    _feature(
        "platform_total",
        "research_capability",
        "Number of recognized R&D or industrial platform records.",
        "zero_when_no_event",
    ),
    _feature(
        "platform_weighted_score",
        "research_capability",
        "Platform count weighted by configured national, provincial, or municipal level.",
        "zero_when_no_event",
    ),
    _feature(
        "national_platform_count",
        "research_capability",
        "Number of nationally recognized research platforms.",
        "zero_when_no_event",
    ),
    _feature(
        "platform_type_diversity",
        "research_capability",
        "Number of distinct platform types.",
        "zero_when_no_event",
    ),
    _feature(
        "platform_recency_days",
        "research_capability",
        "Days from the latest platform record to the cutoff.",
        "median_from_training",
    ),
    _feature(
        "program_total",
        "public_support",
        "Number of public support program records.",
        "zero_when_no_event",
    ),
    _feature(
        "program_award_million_cny_log",
        "public_support",
        "Natural log of one plus total synthetic award amount in millions of CNY.",
        "zero_when_no_event",
    ),
    _feature(
        "program_weighted_score",
        "public_support",
        "Program count weighted by configured administrative level.",
        "zero_when_no_event",
    ),
    _feature(
        "program_recent_share",
        "public_support",
        "Share of support programs awarded inside the recent window.",
        "zero_when_no_event",
    ),
    _feature(
        "program_level_diversity",
        "public_support",
        "Number of distinct program administrative levels.",
        "zero_when_no_event",
    ),
    _feature(
        "program_recency_days",
        "public_support",
        "Days from the latest support program to the cutoff.",
        "median_from_training",
    ),
    _feature(
        "external_support_to_revenue_ratio",
        "public_support",
        "Total synthetic award amount divided by revenue.",
        "median_from_training",
    ),
    _feature(
        "financing_total",
        "capital_access",
        "Number of financing events.",
        "zero_when_no_event",
    ),
    _feature(
        "financing_amount_million_cny_log",
        "capital_access",
        "Natural log of one plus total synthetic financing amount in millions of CNY.",
        "zero_when_no_event",
    ),
    _feature(
        "financing_weighted_score",
        "capital_access",
        "Financing events weighted by configured round stage.",
        "zero_when_no_event",
    ),
    _feature(
        "financing_recent_share",
        "capital_access",
        "Share of financing events inside the recent window.",
        "zero_when_no_event",
    ),
    _feature(
        "financing_recency_days",
        "capital_access",
        "Days from the latest financing event to the cutoff.",
        "median_from_training",
    ),
    _feature(
        "investor_count",
        "capital_access",
        "Number of distinct synthetic investors.",
        "zero_when_no_event",
    ),
    _feature(
        "talent_total",
        "talent",
        "Number of recognized talent program records.",
        "zero_when_no_event",
    ),
    _feature(
        "talent_weighted_score",
        "talent",
        "Talent records weighted by configured administrative level.",
        "zero_when_no_event",
    ),
    _feature(
        "national_talent_share",
        "talent",
        "Share of talent records at national level.",
        "zero_when_no_event",
    ),
    _feature(
        "talent_recency_days",
        "talent",
        "Days from the latest talent record to the cutoff.",
        "median_from_training",
    ),
    _feature(
        "recent_activity_families",
        "composite",
        "Count of event families with at least one event in the recent window.",
        "zero_when_no_event",
    ),
    _feature(
        "ip_per_100_employees",
        "composite",
        "Patents plus software registrations per 100 employees.",
        "median_from_training",
    ),
    _feature(
        "research_platform_per_1000_employees",
        "composite",
        "Research platforms per 1,000 employees.",
        "median_from_training",
    ),
    _feature(
        "funding_to_revenue_ratio",
        "composite",
        "Total synthetic financing divided by revenue.",
        "median_from_training",
    ),
)

FEATURE_COLUMNS: tuple[str, ...] = tuple(
    definition.name for definition in FEATURE_DEFINITIONS
)


def catalog_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [definition.to_dict() for definition in FEATURE_DEFINITIONS]
    )
