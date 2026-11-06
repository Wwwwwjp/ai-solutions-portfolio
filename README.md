# AI Solutions Portfolio

Public, reproducible examples of enterprise AI workflows, data reliability, and evaluation design.

This repository contains independent implementations built with synthetic data. It does not contain employer source code, internal data, customer information, or competition datasets.

## Focus

The projects here are designed around the work of a Forward Deployed Engineer or AI Solutions Engineer:

- translate an ambiguous business process into a testable technical design;
- make data movement and AI-assisted workflows observable and recoverable;
- evaluate correctness, safety, and failure behavior instead of only demonstrating a happy path;
- document limitations and operational trade-offs clearly.

## Projects

| Project | Status | What it demonstrates |
| --- | --- | --- |
| [Workflow Reliability](projects/workflow-reliability/) | Runnable | Idempotent synchronization, optimistic concurrency, conflict isolation, audit events, CLI design, and tests |
| [Enterprise Growth Feature Pipeline](projects/enterprise-growth-features/) | Runnable | Multi-source validation, point-in-time aggregation, configurable business weights, train-only imputation, and feature lineage |
| Schema-aware Text-to-SQL Agent | Planned | Schema retrieval, read-only execution, guardrails, and reproducible evaluation |
| Supply Chain Exception Intelligence | Planned | Multi-source reconciliation, exception scoring, alert routing, and analyst feedback |

Both runnable projects use synthetic data and do not require API keys or external services. Workflow Reliability uses only the Python standard library; Enterprise Growth Feature Pipeline uses pandas.

## Quick Start

```bash
cd projects/workflow-reliability
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v

workflow-reliability \
  --source examples/source_records.json \
  --target examples/target_records.json
```

The CLI is a dry run by default. Add `--apply` to emit create, update, conflict, and orphan audit events, or `--apply --output /tmp/reconciled.json` to also write the updated target file.

The second project runs a full multi-source feature build:

```bash
cd projects/enterprise-growth-features
python -m pip install -e .
enterprise-features \
  --input-dir examples/data \
  --as-of 2025-06-30 \
  --train-ids examples/data/train_company_ids.txt \
  --output-dir artifacts
```

## Repository Map

```text
.
├── .github/workflows/ci.yml
├── docs/
│   ├── portfolio-strategy.md
│   ├── project-template.md
│   └── publication-checklist.md
├── projects/
│   ├── README.md
│   ├── enterprise-growth-features/
│   └── workflow-reliability/
└── README.md
```

## Engineering Principles

1. **Synthetic by default.** Public examples must not depend on confidential data.
2. **Reproducible before impressive.** Every runnable project includes setup instructions and tests.
3. **Failure paths are part of the design.** Conflicts, retries, invalid input, and partial failure are first-class cases.
4. **Claims match evidence.** The repository describes what the code does, not hypothetical business outcomes.
5. **Small and complete beats broad and unfinished.** A project is marked runnable only when it can be executed locally.

## Publication Policy

Before adding code or screenshots, follow [the publication checklist](docs/publication-checklist.md). Any material derived from an employer, customer, vendor, or competition must be independently rebuilt with synthetic data and reviewed for confidentiality and ownership.

## Author

[Jiapeng Wang](https://github.com/Wwwwwjp)
