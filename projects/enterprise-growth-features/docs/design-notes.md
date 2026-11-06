# Design Notes

## Why Point-in-Time Features Matter

A feature is only valid if it could have been known at the decision time. For example, a patent filed after a scoring cutoff must not influence a score for that cutoff. Every event table is filtered with the same `as_of` timestamp before aggregation.

The sample data includes future rows on purpose. The quality report exposes both input row counts and excluded future rows, making leakage prevention observable instead of implicit.

## Entity Grain

Every event is aggregated to one `company_id`. The loader rejects orphan events rather than silently dropping them. This makes the entity boundary explicit and prevents rows from disappearing during a many-to-one join.

The project intentionally does not attempt fuzzy company-name matching. Entity resolution is a separate problem and needs its own thresholds, review workflow, and evaluation set.

## Missing-Value Semantics

The pipeline does not use one fill rule for every feature.

- Event counts use zero when a company has no record in a source because the absence is observed.
- Shares use zero when there is no denominator, while the corresponding count disambiguates no activity.
- Recency and continuous company attributes use medians fitted only on training company IDs.
- A missing R&D staffing ratio receives an explicit missing indicator.

This avoids the original notebook pattern of filling every column with zero and then losing the difference between “no event” and “unknown event.”

## Business Weights

Patent type, patent status, platform level, support-program level, talent level, and financing stage have configurable weights in `data/feature_weights.json`.

These weights are transparent business heuristics. They are not learned parameters and should not be described as statistically validated coefficients. A production system should version the configuration and evaluate sensitivity to alternative weights.

## Training-Scope Preprocessing

The CLI accepts a list of training company IDs. Medians are calculated only from those rows, then applied to the full cohort. This is a small but important leak-prevention boundary: evaluation rows cannot influence their own imputation values.

## Why No Model

The original project also included model training and parameter tuning. This public version stops before modeling so that the repository can focus on:

- multi-source data validation;
- feature lineage;
- time-aware aggregation;
- missing-value policy;
- reproducibility.

Adding a model without a credible evaluation design would make the project look more complete without making the evidence stronger.
