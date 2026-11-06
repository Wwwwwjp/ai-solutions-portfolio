"""Load and validate synthetic enterprise source tables."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .models import DataQualityError, DatasetBundle, SourceAudit


COMPANY_REQUIRED_COLUMNS = {
    "company_id",
    "company_name",
    "sector",
    "province",
    "founded_at",
    "employees",
    "registered_capital_million_cny",
    "rd_staff_ratio",
    "revenue_million_cny",
}

EVENT_REQUIRED_COLUMNS: dict[str, set[str]] = {
    "patents": {"company_id", "event_date", "patent_type", "status"},
    "trademarks": {"company_id", "event_date", "status"},
    "software_copyrights": {"company_id", "event_date"},
    "platforms": {"company_id", "event_date", "platform_type", "level"},
    "programs": {
        "company_id",
        "event_date",
        "program_type",
        "level",
        "award_amount_million_cny",
    },
    "financings": {
        "company_id",
        "event_date",
        "round_type",
        "amount_million_cny",
        "investor_id",
    },
    "talent": {"company_id", "event_date", "talent_type", "level"},
}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise DataQualityError(f"missing input file: {path}")
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    except (OSError, pd.errors.ParserError) as exc:
        raise DataQualityError(f"cannot read {path}: {exc}") from exc


def _require_columns(
    frame: pd.DataFrame,
    required: Iterable[str],
    path: Path,
) -> None:
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise DataQualityError(
            f"{path.name} is missing columns: {', '.join(missing)}"
        )


def _clean_identifier(series: pd.Series, column: str, path: Path) -> pd.Series:
    cleaned = series.astype(str).str.strip()
    invalid = cleaned.eq("")
    if invalid.any():
        raise DataQualityError(f"{path.name}.{column} contains empty values")
    return cleaned


def _numeric(
    series: pd.Series,
    column: str,
    path: Path,
    *,
    allow_missing: bool,
) -> pd.Series:
    cleaned = series.astype(str).str.strip()
    parsed = pd.to_numeric(cleaned, errors="coerce")
    invalid = parsed.isna() & cleaned.ne("")
    if invalid.any():
        raise DataQualityError(f"{path.name}.{column} contains non-numeric values")
    if not allow_missing and parsed.isna().any():
        raise DataQualityError(f"{path.name}.{column} contains missing values")
    return parsed.astype(float)


def _dates(series: pd.Series, column: str, path: Path) -> pd.Series:
    parsed = pd.to_datetime(series.astype(str).str.strip(), errors="coerce")
    if parsed.isna().any():
        raise DataQualityError(f"{path.name}.{column} contains invalid dates")
    return parsed.dt.normalize()


def _validate_company_ids(
    frame: pd.DataFrame,
    company_ids: set[str],
    path: Path,
) -> None:
    orphaned = sorted(set(frame["company_id"]) - company_ids)
    if orphaned:
        preview = ", ".join(orphaned[:5])
        raise DataQualityError(
            f"{path.name} contains unknown company_id values: {preview}"
        )


def _load_companies(
    path: Path,
    as_of: pd.Timestamp,
) -> tuple[pd.DataFrame, SourceAudit]:
    raw = _read_csv(path)
    _require_columns(raw, COMPANY_REQUIRED_COLUMNS, path)
    if raw.empty:
        raise DataQualityError(f"{path.name} must contain at least one company")

    frame = raw.copy()
    for column in ("company_id", "company_name", "sector", "province"):
        frame[column] = _clean_identifier(frame[column], column, path)

    duplicate_ids = frame.loc[frame["company_id"].duplicated(), "company_id"]
    if not duplicate_ids.empty:
        raise DataQualityError(
            "duplicate company_id values: "
            + ", ".join(sorted(duplicate_ids.unique())[:5])
        )

    frame["founded_at"] = _dates(frame["founded_at"], "founded_at", path)
    frame["employees"] = _numeric(
        frame["employees"], "employees", path, allow_missing=False
    )
    frame["registered_capital_million_cny"] = _numeric(
        frame["registered_capital_million_cny"],
        "registered_capital_million_cny",
        path,
        allow_missing=True,
    )
    frame["rd_staff_ratio"] = _numeric(
        frame["rd_staff_ratio"], "rd_staff_ratio", path, allow_missing=True
    )
    frame["revenue_million_cny"] = _numeric(
        frame["revenue_million_cny"],
        "revenue_million_cny",
        path,
        allow_missing=True,
    )

    if (frame["employees"] < 0).any():
        raise DataQualityError(f"{path.name}.employees must be non-negative")
    if (frame["founded_at"] > as_of).any():
        raise DataQualityError(f"{path.name}.founded_at must not be after the cutoff")
    if frame["rd_staff_ratio"].dropna().between(0, 1).eq(False).any():
        raise DataQualityError(f"{path.name}.rd_staff_ratio must be between 0 and 1")
    for column in (
        "registered_capital_million_cny",
        "revenue_million_cny",
    ):
        if (frame[column].dropna() < 0).any():
            raise DataQualityError(f"{path.name}.{column} must be non-negative")

    return frame, SourceAudit(
        file=path.name,
        input_rows=len(raw),
        rows_at_cutoff=len(frame),
        excluded_future_rows=0,
    )


def _load_event_table(
    path: Path,
    required_columns: set[str],
    as_of: pd.Timestamp,
    company_ids: set[str],
) -> tuple[pd.DataFrame, SourceAudit]:
    raw = _read_csv(path)
    _require_columns(raw, required_columns, path)

    frame = raw.copy()
    frame["company_id"] = _clean_identifier(
        frame["company_id"], "company_id", path
    )
    frame["event_date"] = _dates(frame["event_date"], "event_date", path)
    _validate_company_ids(frame, company_ids, path)

    for column in ("patent_type", "status", "platform_type", "level"):
        if column in frame.columns:
            frame[column] = _clean_identifier(frame[column], column, path)
    for column in ("program_type", "round_type", "talent_type", "investor_id"):
        if column in frame.columns:
            frame[column] = _clean_identifier(frame[column], column, path)

    for column in ("award_amount_million_cny", "amount_million_cny"):
        if column in frame.columns:
            frame[column] = _numeric(
                frame[column], column, path, allow_missing=True
            )
            if (frame[column].dropna() < 0).any():
                raise DataQualityError(
                    f"{path.name}.{column} must be non-negative"
                )

    future_mask = frame["event_date"] > as_of
    visible = frame.loc[~future_mask].reset_index(drop=True)
    return visible, SourceAudit(
        file=path.name,
        input_rows=len(raw),
        rows_at_cutoff=len(visible),
        excluded_future_rows=int(future_mask.sum()),
    )


def load_dataset(input_dir: Path, as_of: pd.Timestamp) -> DatasetBundle:
    """Load all source tables and enforce a single point-in-time cutoff."""
    cutoff = pd.Timestamp(as_of).normalize()
    companies, company_audit = _load_companies(
        input_dir / "companies.csv", cutoff
    )
    company_ids = set(companies["company_id"])

    audit: dict[str, SourceAudit] = {"companies": company_audit}
    events: dict[str, pd.DataFrame] = {}
    for name, required in EVENT_REQUIRED_COLUMNS.items():
        path = input_dir / f"{name}.csv"
        frame, source_audit = _load_event_table(
            path,
            required,
            cutoff,
            company_ids,
        )
        events[name] = frame
        audit[name] = source_audit

    return DatasetBundle(
        as_of=cutoff,
        companies=companies,
        events=events,
        audit=audit,
    )
