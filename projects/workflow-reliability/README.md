# Workflow Reliability

A small reference implementation for synchronizing business records between an upstream source and an operational target without silently applying conflicting updates.

The project is an independent, synthetic-data example. It does not connect to Jira, Excel, Power BI, or any employer system.

## Problem

Operational workflows often combine an upstream system of record with spreadsheets, dashboards, or task trackers. Retries and concurrent edits can cause:

- duplicate creates;
- stale updates overwriting newer work;
- silent divergence when two systems use the same version;
- repeated application of the same change;
- missing records without an explicit deletion policy.

This project makes those cases explicit instead of hiding them behind a successful HTTP response.

## What It Demonstrates

- deterministic reconciliation based on record key and version;
- optimistic concurrency control;
- isolation of same-version field divergence;
- orphan detection without implicit deletion;
- idempotent replay;
- structured audit events;
- a dependency-free CLI;
- unit tests for normal and failure paths.

## Architecture

```text
source records ──┐
                 ├──> reconcile ──> create/update/unchanged/conflict/orphan
target records ──┘                         │
                                           ├──> dry-run summary
                                           └──> apply ──> updated target + audit events
```

### Conflict Rules

| Source | Target | Outcome |
| --- | --- | --- |
| Present | Missing | Create |
| Version higher | Version lower | Update |
| Version lower | Version higher | Conflict: target is ahead |
| Same version, same fields | Same version, same fields | Unchanged |
| Same version, different fields | Same version, different fields | Conflict: divergent versions |
| Missing | Present | Orphan; never deleted automatically |

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

workflow-reliability \
  --source examples/source_records.json \
  --target examples/target_records.json
```

Example output:

```json
{
  "conflicts": 1,
  "creates": 1,
  "orphaned": 1,
  "unchanged": 1,
  "updates": 1
}
```

Apply the plan and write the merged target:

```bash
workflow-reliability \
  --source examples/source_records.json \
  --target examples/target_records.json \
  --apply \
  --output /tmp/reconciled.json
```

The command is a dry run unless `--apply` is provided. `--apply` emits audit events; adding `--output` writes the updated target file.

Conflicts remain untouched and are reported to the caller.

## Test

```bash
python -m unittest discover -s tests -v
```

## Design Decisions

### Version-based optimistic concurrency

The implementation compares source and target versions instead of using timestamps alone. Timestamps are useful for display but are vulnerable to clock skew and equal-time collisions.

### No implicit deletion

A missing source record is reported as an orphan. Source feeds are often partial, so treating absence as deletion could remove valid operational records.

### Conflict isolation

Field-level merging is intentionally not automatic. Without domain ownership rules, silently combining two divergent records can create a result that neither system approved.

### Standard library only

The example avoids infrastructure dependencies so reviewers can inspect the core control flow. A production connector would still need authentication, pagination, retry policy, rate limiting, and observability.

## Limitations

- This is not a production connector.
- Version numbers must be assigned by the source system.
- Conflicts require a human or domain-specific resolution policy.
- The CLI loads data into memory and is not designed for very large datasets.
- There is no deletion, access control, schema registry, or transactional database layer.

## Next Steps

- Add a persisted idempotency ledger.
- Add pluggable resolution policies with audit trails.
- Add adapters for a database and a spreadsheet-like target.
- Add property-based tests for reconciliation invariants.
- Add metrics for conflicts, retries, and time-to-resolution.
