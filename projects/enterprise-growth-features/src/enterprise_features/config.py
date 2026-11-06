"""Feature weight configuration."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
import json
from pathlib import Path
from typing import Any, Mapping

from .models import DataQualityError


def _require_weight_map(
    payload: Mapping[str, Any],
    key: str,
) -> dict[str, float]:
    raw = payload.get(key)
    if not isinstance(raw, Mapping) or not raw:
        raise DataQualityError(f"{key} must be a non-empty object")

    result: dict[str, float] = {}
    for label, value in raw.items():
        if not isinstance(label, str) or not label.strip():
            raise DataQualityError(f"{key} contains an invalid label")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise DataQualityError(f"{key}.{label} must be numeric")
        if value < 0:
            raise DataQualityError(f"{key}.{label} must be non-negative")
        result[label] = float(value)
    return result


@dataclass(frozen=True)
class FeatureConfig:
    version: str
    recent_window_days: int
    patent_type_weights: Mapping[str, float]
    patent_status_weights: Mapping[str, float]
    platform_level_weights: Mapping[str, float]
    program_level_weights: Mapping[str, float]
    talent_level_weights: Mapping[str, float]
    financing_round_weights: Mapping[str, float]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FeatureConfig":
        version = payload.get("version")
        recent_window_days = payload.get("recent_window_days")

        if not isinstance(version, str) or not version.strip():
            raise DataQualityError("version must be a non-empty string")
        if (
            not isinstance(recent_window_days, int)
            or isinstance(recent_window_days, bool)
            or recent_window_days <= 0
        ):
            raise DataQualityError("recent_window_days must be a positive integer")

        return cls(
            version=version,
            recent_window_days=recent_window_days,
            patent_type_weights=_require_weight_map(
                payload, "patent_type_weights"
            ),
            patent_status_weights=_require_weight_map(
                payload, "patent_status_weights"
            ),
            platform_level_weights=_require_weight_map(
                payload, "platform_level_weights"
            ),
            program_level_weights=_require_weight_map(
                payload, "program_level_weights"
            ),
            talent_level_weights=_require_weight_map(
                payload, "talent_level_weights"
            ),
            financing_round_weights=_require_weight_map(
                payload, "financing_round_weights"
            ),
        )


def _load_payload(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataQualityError(f"cannot read config {path}: {exc}") from exc

    if not isinstance(payload, Mapping):
        raise DataQualityError("feature config must contain a JSON object")
    return payload


def load_config(path: Path) -> FeatureConfig:
    return FeatureConfig.from_dict(_load_payload(path))


def load_default_config() -> FeatureConfig:
    resource = resources.files("enterprise_features").joinpath(
        "data/feature_weights.json"
    )
    with resource.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise DataQualityError("feature config must contain a JSON object")
    return FeatureConfig.from_dict(payload)
