"""Leakage-safe feature engineering for multi-source enterprise activity."""

from .aggregation import build_feature_table
from .config import FeatureConfig, load_config, load_default_config
from .pipeline import FeaturePipeline, PipelineResult
from .sources import DataQualityError, DatasetBundle, load_dataset

__all__ = [
    "DataQualityError",
    "DatasetBundle",
    "FeatureConfig",
    "FeaturePipeline",
    "PipelineResult",
    "build_feature_table",
    "load_config",
    "load_dataset",
    "load_default_config",
]
