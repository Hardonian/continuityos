from __future__ import annotations

from datetime import UTC, datetime
from math import isfinite, sqrt

from pydantic import BaseModel, Field, field_validator


class RegressionRow(BaseModel):
    """One time-aligned outcome/indicator row with explicit source provenance."""

    observed_at: datetime
    target: float
    features: dict[str, float] = Field(min_length=2, max_length=64)
    source_ids: list[str] = Field(min_length=1, max_length=32)
    snapshot_ids: list[str] = Field(min_length=1, max_length=32)

    @field_validator("observed_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        return value

    @field_validator("target")
    @classmethod
    def finite_target(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("target must be finite")
        return value

    @field_validator("features")
    @classmethod
    def finite_features(cls, value: dict[str, float]) -> dict[str, float]:
        if not value:
            raise ValueError("features cannot be empty")
        if any(not isfinite(item) for item in value.values()):
            raise ValueError("all feature values must be finite")
        return value


class RegressionRequest(BaseModel):
    dataset_id: str = Field(min_length=2, max_length=128)
    target_name: str = Field(min_length=2, max_length=128)
    rows: list[RegressionRow] = Field(min_length=8, max_length=10000)
    ridge_alpha: float = Field(default=0.1, ge=0.0, le=1_000_000.0)
    test_fraction: float = Field(default=0.2, gt=0.0, lt=0.5)


class RegressionCoefficient(BaseModel):
    feature: str
    coefficient: float
    standardized_effect: float
    train_mean: float
    train_stddev: float


class RegressionResult(BaseModel):
    dataset_id: str
    target_name: str
    row_count: int
    feature_count: int
    train_row_count: int
    test_row_count: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    ridge_alpha: float
    coefficients: list[RegressionCoefficient]
    intercept: float
    test_rmse: float
    test_mae: float
    test_r2: float | None
    source_ids: list[str]
    snapshot_ids: list[str]
    limitations: list[str]


def _transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(column) for column in zip(*matrix, strict=False)]


def _matmul(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    return [
        [
            sum(left_row[k] * right[k][column] for k in range(len(right)))
            for column in range(len(right[0]))
        ]
        for left_row in left
    ]


def _solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    augmented = [[*row[:], value] for row, value in zip(matrix, vector, strict=False)]
    size = len(augmented)
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("regression design matrix is singular; increase ridge_alpha")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                current - factor * pivot_value
                for current, pivot_value in zip(augmented[row], augmented[column], strict=False)
            ]
    return [augmented[row][-1] for row in range(size)]


def run_regression(request: RegressionRequest) -> RegressionResult:
    ordered = sorted(request.rows, key=lambda row: row.observed_at.astimezone(UTC))
    feature_names = sorted(ordered[0].features)
    if len(feature_names) < 2:
        raise ValueError("at least two indicators are required for multivariate regression")
    if any(sorted(row.features) != feature_names for row in ordered):
        raise ValueError("every row must contain exactly the same feature names")
    if len(ordered) < max(8, len(feature_names) + 4):
        raise ValueError("insufficient rows for the requested feature count")

    split = int(len(ordered) * (1.0 - request.test_fraction))
    split = min(max(split, len(feature_names) + 2), len(ordered) - 2)
    train, test = ordered[:split], ordered[split:]
    means = [sum(row.features[name] for row in train) / len(train) for name in feature_names]
    stddevs = []
    for index, name in enumerate(feature_names):
        variance = sum((row.features[name] - means[index]) ** 2 for row in train) / max(
            1, len(train) - 1
        )
        stddevs.append(sqrt(variance) or 1.0)

    def design(rows: list[RegressionRow]) -> list[list[float]]:
        return [
            [1.0]
            + [
                (row.features[name] - means[index]) / stddevs[index]
                for index, name in enumerate(feature_names)
            ]
            for row in rows
        ]

    x_train, x_test = design(train), design(test)
    y_train = [row.target for row in train]
    gram = _matmul(_transpose(x_train), x_train)
    for index in range(1, len(gram)):
        gram[index][index] += request.ridge_alpha
    rhs = [
        sum(x_train[row][column] * y_train[row] for row in range(len(train)))
        for column in range(len(gram))
    ]
    weights = _solve(gram, rhs)
    predictions = [
        sum(value * weight for value, weight in zip(row, weights, strict=False)) for row in x_test
    ]
    residuals = [
        prediction - row.target for prediction, row in zip(predictions, test, strict=False)
    ]
    mae = sum(abs(value) for value in residuals) / len(residuals)
    rmse = sqrt(sum(value * value for value in residuals) / len(residuals))
    target_mean = sum(row.target for row in test) / len(test)
    total = sum((row.target - target_mean) ** 2 for row in test)
    r2 = None if total <= 1e-12 else 1.0 - sum(value * value for value in residuals) / total
    all_sources = sorted({source for row in ordered for source in row.source_ids})
    all_snapshots = sorted({snapshot for row in ordered for snapshot in row.snapshot_ids})

    return RegressionResult(
        dataset_id=request.dataset_id,
        target_name=request.target_name,
        row_count=len(ordered),
        feature_count=len(feature_names),
        train_row_count=len(train),
        test_row_count=len(test),
        train_start=train[0].observed_at,
        train_end=train[-1].observed_at,
        test_start=test[0].observed_at,
        test_end=test[-1].observed_at,
        ridge_alpha=request.ridge_alpha,
        coefficients=[
            RegressionCoefficient(
                feature=name,
                coefficient=weights[index + 1] / stddevs[index],
                standardized_effect=weights[index + 1],
                train_mean=means[index],
                train_stddev=stddevs[index],
            )
            for index, name in enumerate(feature_names)
        ],
        intercept=weights[0],
        test_rmse=rmse,
        test_mae=mae,
        test_r2=r2,
        source_ids=all_sources,
        snapshot_ids=all_snapshots,
        limitations=[
            "Associational model; coefficients are not causal effects or intelligence judgments.",
            "Temporal holdout is used, but this is not a validated operational forecast.",
            (
                "Results depend on source quality, coverage, normalization, confounding, "
                "and selection bias."
            ),
            (
                "Human review and domain-specific validation are required before any "
                "consequential use."
            ),
        ],
    )
