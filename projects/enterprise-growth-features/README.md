# Enterprise Growth Feature Pipeline

A point-in-time feature engineering pipeline that turns fragmented enterprise activity records into one auditable, model-ready table.

This is an independent, synthetic rebuild inspired by a 2023 fintech training-camp team project. The original exercise combined dozens of public innovation signals to describe enterprise growth potential. This repository contains no bank, customer, employer, or competition data and no copied notebook code. It is not a deployed financial product.

The original team exercise worked across 47 source groups and reduced a 226-column raw matrix to 27 business features. This rebuild focuses on the engineering discipline behind that work: entity alignment, time cutoffs, transparent weights, missing-value policy, feature lineage, and reproducibility.

## Problem

Enterprise growth signals arrive as separate tables with different grains:

- patents and trademarks;
- software copyright registrations;
- research platforms;
- public support programs;
- financing events;
- talent programs;
- company profile attributes.

A naive pipeline creates label leakage, silently treats missing activity as zero, mixes entities, or loses the reason behind derived scores. This project makes those decisions explicit and testable.

## What It Demonstrates

- one canonical company key across eight source tables;
- a strict point-in-time cutoff for every event table;
- event-to-company aggregation with counts, recency, frequency, diversity, and shares;
- configurable business weights for patent status, administrative level, and financing stage;
- train-scope-only median imputation;
- distinct missing-value policies for counts, ratios, and recency;
- a generated feature catalog and data-quality report;
- a dependency-light CLI with automated tests for leakage and data contracts.

## Architecture

```text
companies + 7 event tables
          │
          ├── schema validation
          ├── as-of future-row exclusion
          └── company-level aggregation
                     │
                     ├── business weights
                     ├── recency / frequency / diversity
                     └── ratios and composite signals
                                │
                                ├── feature_catalog.csv
                                ├── quality_report.json
                                └── leakage-safe features.csv
```

The sample contains:

- 42 fictional companies;
- 8 source tables;
- 46 engineered features across 8 families;
- 22 future-dated records that are intentionally excluded at the demo cutoff.

## Feature Families

| Family | Examples |
| --- | --- |
| Company profile | company age, log employees, log registered capital, R&D staffing ratio |
| Intellectual property | patent count and weighted score, active share, invention share, trademark and software recency |
| Research capability | platform count, level-weighted score, national platform count, diversity |
| Public support | award amount, program count, administrative-level score, award-to-revenue ratio |
| Capital access | financing count, amount, stage-weighted score, investor count, recency |
| Talent | talent count, level-weighted score, national talent share |
| Composite | recent activity breadth, IP per employee, research platforms per employee |
| Data quality | explicit missing indicator for the R&D staffing ratio |

Every output feature is defined in the generated `feature_catalog.csv`.

## Input Contract

All source files live in one directory and use `company_id` as the join key.

| File | Grain | Required fields |
| --- | --- | --- |
| `companies.csv` | one row per company | company ID, profile, founding date, employees, capital, revenue, R&D ratio |
| `patents.csv` | one row per patent | event date, patent type, status |
| `trademarks.csv` | one row per trademark | event date, status |
| `software_copyrights.csv` | one row per registration | event date |
| `platforms.csv` | one row per recognized platform | event date, platform type, level |
| `programs.csv` | one row per support event | event date, program type, level, award amount |
| `financings.csv` | one row per financing round | event date, round type, amount, investor ID |
| `talent.csv` | one row per talent recognition | event date, talent type, level |

The loader rejects duplicate company IDs, orphan event rows, invalid dates, invalid numeric values, missing columns, and event categories that have no configured weight.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

python examples/generate_synthetic_data.py

enterprise-features \
  --input-dir examples/data \
  --as-of 2025-06-30 \
  --train-ids examples/data/train_company_ids.txt \
  --output-dir artifacts
```

The command writes:

```text
artifacts/
├── feature_catalog.csv
├── features.csv
└── quality_report.json
```

`features.csv` contains identifiers plus the 46 engineered features. The quality report records source row counts, excluded future rows, pre-imputation missing rates, and the medians learned from the training company IDs.

## Test

```bash
python -m unittest discover -s tests -v
```

The tests cover:

- future-event exclusion at the point-in-time cutoff;
- duplicate and orphan company keys;
- configured patent weights and shares;
- train-scope-only imputation;
- no-event zero semantics;
- rejection of unmapped categories;
- catalog/output alignment and finite output values.

## What Changed from a Notebook Workflow

| Notebook pattern | Portfolio implementation |
| --- | --- |
| Hardcoded Windows and collaborator paths | CLI input directory |
| A separate script block per source table | Validated source loaders and shared event contract |
| `2023 - timestamp` recency | Explicit `--as-of` cutoff |
| Global `fillna(0)` | Separate policies for counts, ratios, and continuous fields |
| `inf` replaced with an arbitrary constant | Invalid ratios become missing and use a learned median |
| `LabelEncoder` over administrative levels | Explicit, inspectable weight configuration |
| Ad hoc feature list | Generated feature catalog with names, families, and missing policy |
| Full-data imputation | Medians fitted on training company IDs only |
| No automated checks | Leakage, schema, weighting, and output-contract tests |

## Limitations

- The data is synthetic and does not support claims about real enterprises or credit risk.
- The weights encode business heuristics; they are not statistically estimated or causal.
- This project stops at feature generation and does not train or validate a predictive model.
- Entity resolution beyond an exact `company_id` is intentionally out of scope.
- The implementation is optimized for review and reproducibility, not large-scale distributed processing.
- A production version would add a warehouse adapter, schema registry, feature store, monitoring, and access controls.

## Next Steps

- Add a model-evaluation project that consumes this feature table without leakage.
- Add dbt or SQL implementations of the same feature definitions for warehouse execution.
- Add drift and coverage monitoring per feature family.
- Add synthetic entity-resolution cases with near-duplicate company names.
