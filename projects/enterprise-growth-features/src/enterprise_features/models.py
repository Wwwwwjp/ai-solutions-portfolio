"""Shared data structures and feature metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import pandas as pd


class DataQualityError(ValueError):
    """Raised when an input file violates the feature pipeline contract."""


@dataclass(frozen=True)
class SourceAudit:
    file: str
    input_rows: int
    rows_at_cutoff: int
    excluded_future_rows: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "file": self.file,
            "input_rows": self.input_rows,
            "rows_at_cutoff": self.rows_at_cutoff,
            "excluded_future_rows": self.excluded_future_rows,
        }


@dataclass(frozen=True)
class DatasetBundle:
    as_of: pd.Timestamp
    companies: pd.DataFrame
    events: Mapping[str, pd.DataFrame]
    audit: Mapping[str, SourceAudit]


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    family: str
    description: str
    missing_policy: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "family": self.family,
            "description": self.description,
            "missing_policy": self.missing_policy,
        }
