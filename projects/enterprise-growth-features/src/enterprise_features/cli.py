"""Command line interface for the feature pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from .catalog import catalog_frame
from .config import load_config, load_default_config
from .models import DataQualityError
from .pipeline import run_feature_pipeline
from .sources import load_dataset


def _train_ids(path: Path | None, fallback: Iterable[str]) -> list[str]:
    if path is None:
        return list(fallback)
    try:
        ids = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except OSError as exc:
        raise DataQualityError(f"cannot read training ids: {exc}") from exc
    if not ids:
        raise DataQualityError(f"training id file is empty: {path}")
    return ids


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="enterprise-features",
        description=(
            "Build point-in-time enterprise growth features from synthetic source tables."
        ),
    )
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument(
        "--as-of",
        required=True,
        help="point-in-time cutoff in YYYY-MM-DD format",
    )
    parser.add_argument("--train-ids", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts"),
    )
    return parser


def main() -> int:
    parser = _parser()
    args = parser.parse_args()

    try:
        config = (
            load_config(args.config)
            if args.config is not None
            else load_default_config()
        )
        bundle = load_dataset(args.input_dir, args.as_of)
        ids = _train_ids(args.train_ids, bundle.companies["company_id"])
        result = run_feature_pipeline(bundle, config, ids)

        args.output_dir.mkdir(parents=True, exist_ok=True)
        result.features.to_csv(
            args.output_dir / "features.csv",
            index=False,
            float_format="%.8g",
        )
        catalog_frame().to_csv(
            args.output_dir / "feature_catalog.csv",
            index=False,
        )
        (args.output_dir / "quality_report.json").write_text(
            json.dumps(result.report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (DataQualityError, OSError, ValueError) as exc:
        parser.error(str(exc))

    summary = {
        "as_of": result.report["as_of"],
        "companies": result.report["company_count"],
        "features": result.report["feature_count"],
        "training_companies": result.report["training_company_count"],
        "output_dir": str(args.output_dir),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
