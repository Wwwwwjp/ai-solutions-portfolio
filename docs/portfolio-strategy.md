# Portfolio Strategy

## Objective

Show evidence for Forward Deployed Engineer and AI Solutions Engineer roles through public, executable work. The portfolio should make technical judgment visible without exposing confidential material.

## Recommended Narrative

The portfolio should support four claims:

1. I can understand a business workflow and turn it into explicit system behavior.
2. I can build data and AI workflows that handle retries, conflicts, invalid input, and partial failure.
3. I can evaluate solution quality rather than relying on a polished demo.
4. I can explain trade-offs and limitations to both technical and business audiences.

## Project Sequence

### 1. Workflow Reliability

Status: runnable.

Demonstrates deterministic synchronization between an upstream source and an operational target. It covers creates, updates, equal-version conflicts, stale targets, orphaned records, idempotent replay, and audit events.

### 2. Schema-aware Text-to-SQL Agent

Status: planned.

Should include:

- schema discovery and relevant-table selection;
- read-only query execution;
- SQL validation and bounded result sizes;
- a small gold dataset for exact-match and execution-match evaluation;
- failure injection for ambiguous questions, unsafe SQL, and empty results;
- a deterministic test model so the project runs without paid APIs.

### 3. Supply Chain Exception Intelligence

Status: planned.

Should include:

- synthetic multi-source allocation data;
- configurable tolerance and aging rules;
- explainable exception scoring;
- alert routing with deduplication;
- analyst feedback capture;
- a reproducible evaluation of false positives and missed exceptions.

## What Not to Publish

- Employer code, internal field names, screenshots, system diagrams, or business data.
- Customer, supplier, employee, or partner information.
- Competition data or submissions whose terms restrict redistribution.
- Metrics that cannot be verified or that describe expected rather than realized outcomes.
- Large notebooks without tests, data provenance, or a runnable path.

## Quality Bar

A project is portfolio-ready only when it has:

- a clear problem statement and non-goals;
- a reproducible local setup;
- automated tests covering normal and failure paths;
- synthetic or correctly licensed sample data;
- explicit security and operational limitations;
- a short architecture explanation and design trade-offs;
- no personal contact information or confidential material.
