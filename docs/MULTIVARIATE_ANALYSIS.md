# Multivariate Indicator Analysis

## Purpose

ContinuityOS now exposes a bounded multivariate ridge-regression analysis endpoint for a time-aligned dataset of normalized indicators. It is designed for exploratory continuity analysis and model validation, not intelligence production, causal inference, autonomous control, or operational forecasting.

Endpoint:

```text
POST /v1/analysis/regression
```

Authentication: `X-Continuity-API-Key` in the reference deployment.

## Input contract

Each row contains:

- timezone-aware `observed_at`;
- one finite target outcome, such as delay, shortage, recovery time, or continuity score;
- two or more named finite features;
- one or more source IDs;
- one or more content-addressed snapshot IDs.

Every row must contain the exact same feature names. Missing values are rejected rather than silently imputed. The source and snapshot lists are retained in the signed evidence record.

## Method

1. Sort rows chronologically.
2. Split the newest fraction into a temporal holdout test set.
3. Standardize features using training-set means and standard deviations only.
4. Fit ridge regression with an explicit configurable penalty.
5. Report coefficients, standardized effects, intercept, MAE, RMSE, and optional test R².
6. Record source IDs, snapshot IDs, training/test windows, and limitations in the evidence ledger.

This avoids random shuffling and reduces leakage from future observations, but it does not solve confounding, selection bias, non-stationarity, measurement error, source correlation, or policy changes.

## Indicator families

The initial catalog supports features from:

- environmental: sea ice, weather, wind, waves, wildfire, floods, water levels, climate anomalies;
- maritime: historic traffic, port geometry, water depth/context, route conditions;
- space/satellite: EO observation coverage and orbital geometry context;
- communications: authenticated SATCOM availability and operator service telemetry;
- cyber: authenticated cyber-control health and data integrity;
- trade/supply chain: trade dependency, supplier concentration, lead times, inventory days;
- governance/policy: structured analyst assessments with explicit confidence and provenance;
- resilience actions: escort capacity, alternate routes, substitution and recovery indicators.

The regression endpoint does not automatically assert that a source is allowed to produce a given metric. Source-policy validation remains required at ingestion and observation creation.

## What a serious evaluation requires

A credible pilot should maintain:

- a pre-registered target definition;
- a versioned feature dictionary and normalization rules;
- source and snapshot completeness checks;
- temporal train/test splits appropriate to the decision horizon;
- rolling-origin backtesting;
- baseline models and null comparisons;
- calibration and uncertainty intervals;
- subgroup and geography checks;
- missingness and stale-data analysis;
- drift detection;
- analyst review of outliers and data poisoning;
- an outcome-label collection process;
- a human approval record for every consequential use.

The current endpoint is the first bounded analytic primitive. It is not the final production statistical stack. A production tenant should add a database-backed feature store, model registry, reproducible compute environment, model cards, monitoring, and independent validation.

## Prohibited interpretations

Do not describe a coefficient as causation, threat attribution, adversary intent, intelligence, or proof that an indicator will produce a specific event. Do not use public satellite geometry as a substitute for provider service telemetry. Do not use regression output to control vessels, drones, weapons, OT, communications networks, or emergency actions.
