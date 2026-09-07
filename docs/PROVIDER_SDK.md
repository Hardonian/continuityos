# ContinuityOS Provider SDK & Normalization Architecture

The ContinuityOS Provider SDK decouples the core Continuity-as-Code engine from external data sources, proprietary APIs, and third-party vendors. Providers fetch, normalize, validate, and cryptographically stamp operational observations into standard `Observation` models.

---

## 1. Provider Core Interface (`base.py`)

All providers subclass `continuityos.providers.base.Provider`:

```python
from abc import ABC, abstractmethod
from datetime import datetime
from continuityos.domain import Observation


class Provider(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for this provider (e.g. 'satcom-iridium-relay')."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""

    @abstractmethod
    def fetch(self, *, as_of: datetime | None = None) -> list[Observation]:
        """Fetch and return normalized, validated observations."""

    @abstractmethod
    def validate(self, observations: list[Observation]) -> list[str]:
        """Validate observations against domain constraints."""

    @property
    def supports_offline(self) -> bool:
        """Indicates whether this provider functions in air-gapped environments."""
        return False
```

---

## 2. Invariant 5: Graceful Degradation Under Failure

A failed external provider must never crash the runtime. Instead, the provider pattern enforces fail-soft handling:
- If a provider times out or throws a connection error, it returns empty observations or degraded confidence records with explicit error notes.
- The downstream functional closure engine flags affected dimensions as degraded or unknown rather than healthy.
- Stale cached snapshots may be used if within allowable freshness windows, accompanied by freshness decay penalties.

---

## 3. Observation Data Contract

Every observation must conform to the strict `Observation` domain contract:

```python
class Observation(BaseModel):
    id: str
    source_id: str
    corridor_id: str
    metric_name: MetricName
    metric_value: float
    unit: str
    observed_at: datetime
    retrieved_at: datetime
    assertion_class: AssertionClass
    source_trust: SourceTrust
    provenance: Provenance
    confidence: float = Field(ge=0.0, le=1.0)
    classification: str = "UNCLASSIFIED"
    signature_status: str = "UNSIGNED"
```

### Provenance Tracking (`Provenance`)
Observations must preserve end-to-end lineage:
- `raw_hash`: SHA-256 hash of the raw upstream API payload.
- `parser_version`: Version of the normalizer used.
- `normalization_method`: Description of unit conversions applied.
- `source_uri`: Endpoint or file path from which data was retrieved.

---

## 4. Built-in Offline Mock Provider (`MockProvider`)

For air-gapped SCIF environments, automated tests, and local evaluation, ContinuityOS includes a zero-dependency `MockProvider`:

```python
from continuityos.providers.mock import MockProvider

# Normal operational baseline
normal_provider = MockProvider(scenario="normal")
observations = normal_provider.fetch()

# Disrupted scenario with GPS jamming and insurance suspension
disrupted_provider = MockProvider(scenario="disrupted")
disrupted_obs = disrupted_provider.fetch()
```

The CLI supports mock ingestion directly:
```bash
continuity observe --mock --scenario disrupted
```

---

## 5. Developing a Custom Provider

Here is an example implementation for an AIS maritime tracking feed:

```python
from datetime import UTC, datetime
import hashlib
from uuid import uuid4
from continuityos.domain import (
    AssertionClass,
    MetricName,
    Observation,
    Provenance,
    SourceTrust,
)
from continuityos.providers.base import Provider


class LiveAISProvider(Provider):
    @property
    def provider_id(self) -> str:
        return "maritime-ais-live"

    @property
    def provider_name(self) -> str:
        return "Live Maritime AIS Feed"

    def fetch(self, *, as_of: datetime | None = None) -> list[Observation]:
        now = as_of or datetime.now(UTC)
        observations = []

        try:
            # 1. Fetch raw vessel telemetry
            raw_payload = b'{"vessel_count": 14, "average_speed_knots": 12.5}'
            payload_hash = hashlib.sha256(raw_payload).hexdigest()

            # 2. Normalize into typed Observation
            observations.append(
                Observation(
                    id=f"obs-{uuid4().hex[:8]}",
                    source_id=self.provider_id,
                    corridor_id="corridor/nsr",
                    metric_name=MetricName.AIS_VESSEL_COUNT,
                    metric_value=14.0,
                    unit="vessels",
                    observed_at=now,
                    retrieved_at=now,
                    assertion_class=AssertionClass.COMMERCIAL_CARRIER,
                    source_trust=SourceTrust.VERIFIED_COMMERCIAL,
                    provenance=Provenance(
                        raw_hash=payload_hash,
                        parser_version="v1.0.0",
                        normalization_method="direct-count",
                        source_uri="ais://stream.maritime.internal",
                    ),
                    confidence=0.95,
                )
            )
        except Exception as e:
            # Fail-soft: log error and return bounded fallback
            return []

        return observations

    def validate(self, observations: list[Observation]) -> list[str]:
        errors = []
        for obs in observations:
            if obs.metric_value < 0:
                errors.append(f"Invalid negative vessel count: {obs.metric_value}")
        return errors
```

---

## 6. Testing Your Provider

Run your provider through the test harness:
```bash
uv run pytest tests/test_providers.py
```
Ensure that:
1. Observations validate against `schemas/resource.schema.json`.
2. Provenance hashes match payload bytes.
3. Errors degrade gracefully without unhandled exceptions.
