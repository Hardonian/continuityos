# ContinuityOS Policy Language Reference (`continuity.io/v1`)

ContinuityOS declares resilience requirements using declarative YAML documents conforming to `apiVersion: continuity.io/v1`. These documents are version-controlled in Git and evaluated deterministically by the reconciliation engine.

---

## 1. Resource Kinds Overview

| Kind | Purpose | Schema File |
| :--- | :--- | :--- |
| `SupplyNetwork` | Declares network nodes, desired redundancy, corridor paths, and inventory reserves | `schemas/resource.schema.json` |
| `ContinuityPolicy` | Declares resilience rules, minimum providers, continuity objectives, and trust limits | `schemas/resource.schema.json` |
| `AssurancePolicy` | Declares multi-dimensional resilience budgets, fault tolerances, and verification gates | `schemas/assurance-policy.schema.json` |
| `RouteSubstitution` | Declares multi-constraint alternate route configurations and capacity thresholds | `schemas/route-substitution.schema.json` |
| `DependencyTrust` | Declares 9-dimensional trust requirements and aggregation strategies | `schemas/trust.schema.json` |
| `Scenario` | Declares correlated disruption events for cascade failure simulation | `schemas/scenario.schema.json` |

---

## 2. Specification Definitions

### 2.1 `SupplyNetwork`
Declares the cyber-physical topology of corridors, facilities, providers, and storage depots.

```yaml
apiVersion: continuity.io/v1
kind: SupplyNetwork
metadata:
  name: northern-critical-supply
  version: "1.0.0"
  labels:
    tier: "tier-1-critical"
    jurisdiction: "arctic-sovereign"

spec:
  corridors:
    - id: corridor/nsr
      name: Northern Sea Route Transit Corridor
      primary: true
      physicalState: OPEN
      nominalCapacityTonnesPerDay: 15000.0

    - id: corridor/atlantic
      name: North Atlantic Maritime Corridor
      primary: false
      physicalState: OPEN
      nominalCapacityTonnesPerDay: 25000.0

  ports:
    - id: port/tromso
      name: Tromso Arctic Logistics Hub
      berthCapacityDailyTonnes: 12000.0
      intermodalRailConnected: true

  communications:
    - id: comm/commercial-leo-a
      type: CommercialLEO
      provider: OrbitNet Global
      upstreamTeleportId: gateway/tromso-uplink

    - id: comm/protected-uhf-b
      type: ProtectedSATCOM
      provider: Sovereign Defense Relay
      upstreamTeleportId: gateway/bodo-bunker

  navigation:
    - id: nav/gnss-primary
      type: GNSS
      constellation: GPS-L5
    - id: nav/inertial-backup
      type: INS
      driftRateDegPerHour: 0.01

  inventories:
    - id: inv/fuel-depot-north
      commodity: Polar Diesel Grade A
      currentStock: 45000.0
      unit: tonnes
      dailyBurnRateNormal: 1000.0
      dailyBurnRateDegraded: 750.0
      dailyBurnRateEmergency: 1600.0
      minimumReserveDays: 30
      criticalReserveDays: 14
```

---

### 2.2 `ContinuityPolicy`
Declares policy rules evaluated against observed state.

```yaml
apiVersion: continuity.io/v1
kind: ContinuityPolicy
metadata:
  name: polar-resilience-rules
spec:
  targetNetworkId: northern-critical-supply
  minimumContinuityScore: 0.95

  rules:
    - id: COMM-001
      description: "Must maintain at least 2 physically independent communications providers"
      targetCategory: communications
      assertion: minimum_independent_providers
      threshold: 2
      severity: CRITICAL

    - id: ROUTE-002
      description: "Primary maritime corridors must remain commercially insurable"
      targetCategory: corridors
      assertion: insurance_required
      severity: HIGH

    - id: INV-003
      description: "Assured replenishment timeline must not exceed 30 days"
      targetCategory: inventories
      assertion: max_assured_replenishment_days
      threshold: 30
      severity: CRITICAL

    - id: TRUST-004
      description: "Navigation trust must meet or exceed 0.90"
      targetCategory: navigation
      assertion: minimum_trust_score
      dimension: navigation_integrity
      threshold: 0.90
      severity: MEDIUM
```

---

### 2.3 `AssurancePolicy`
Quantifies the overall resilience budget across redundancy, source diversity, commercial viability, and recovery lag.

```yaml
apiVersion: continuity.io/v1
kind: AssurancePolicy
metadata:
  name: northern-critical-supply
spec:
  continuityObjective:
    minimum: 0.95

  tolerate:
    corridorLoss: 1
    portLoss: 1
    communicationProviderLoss: 1
    navigationSourceLoss: 2
    observationSourceLoss: 1

  evidence:
    minimumIndependentOperationalSources: 2
    minimumIndependentNavigationSources: 3
    minimumIndependentEnvironmentalSources: 2

  commercial:
    minimumCarrierOptions: 2
    insuranceRequired: true

  inventory:
    minimumReserveDays: 30
    minimumAssuredReplenishmentCycles: 1

  recovery:
    verifyCarrierReturn: true
    verifyBacklogClearance: true
    verifyReserveRestoration: true
```

---

### 2.4 `RouteSubstitution`
Declares operational, physical, and temporal constraints for contingency routing.

```yaml
apiVersion: continuity.io/v1
kind: RouteSubstitution
metadata:
  name: arctic-atlantic-contingency
spec:
  primaryRouteId: corridor/nsr
  alternateRouteId: corridor/atlantic
  candidateName: North Atlantic Maritime Route
  requiredVesselClass: Ice-Class 1A
  originCapacityTonnes: 500000.0
  routeCapacityTonnes: 450000.0
  portHandlingCapacityTonnes: 380000.0
  inlandRailCapacityTonnes: 320000.0
  carrierAvailable: true
  insuranceAvailable: true
  fuelBunkerAvailable: true
  transitDays: 28.0
  criticalArrivalDeadlineDays: 35.0
```

---

### 2.5 `DependencyTrust`
Configures multidimensional trust assertions.

```yaml
apiVersion: continuity.io/v1
kind: DependencyTrust
metadata:
  name: corridor-nsr-trust
spec:
  targetResourceId: corridor/nsr
  aggregationStrategy: minimum  # options: minimum, weighted, mean

  dimensions:
    physicalAvailability: 1.00
    cyberIntegrity: 0.95
    legalAvailability: 1.00
    commercialAvailability: 0.20 # low due to carrier diversion
    communicationsIntegrity: 0.85
    navigationIntegrity: 0.65     # degraded due to GNSS anomalies
    insuranceAvailability: 0.00   # war-risk coverage withdrawn
    operatorConfidence: 0.80
    informationConfidence: 0.90

  weights: # used only when aggregationStrategy is 'weighted'
    physicalAvailability: 0.20
    commercialAvailability: 0.30
    navigationIntegrity: 0.25
    insuranceAvailability: 0.25
```

---

### 2.6 `Scenario`
Models correlated disruptions for cascade analysis.

```yaml
apiVersion: continuity.io/v1
kind: Scenario
metadata:
  name: multi-corridor-disruption
spec:
  description: "Simultaneous GNSS jamming, SATCOM loss, and Red Sea chokepoint diversion"
  events:
    - target: corridor/hormuz
      state: DEGRADED
      effectiveState: OPEN_DEGRADED
      timestamp: "2026-09-07T00:00:00Z"

    - target: corridor/red-sea
      state: FUNCTIONALLY_CLOSED
      effectiveState: FUNCTIONALLY_CLOSED
      timestamp: "2026-09-07T04:00:00Z"

    - target: comm/commercial-leo-a
      state: UNAVAILABLE
      effectiveState: PHYSICALLY_CLOSED
      timestamp: "2026-09-07T06:00:00Z"

    - target: nav/gnss-primary
      state: DEGRADED
      effectiveState: OPEN_BUT_NAVIGATION_UNTRUSTED
      timestamp: "2026-09-07T08:00:00Z"
```

---

## 3. Defense Readiness & Electronic Warfare Policy Declarations

ContinuityOS supports declaring military operational readiness gates and cyber-physical electronic warfare thresholds.

### 3.1 Security Classification & Dissemination Metadata
Specs can enforce mandatory classification labels, compartment tags, and five-eyes / NATO dissemination caveats:

```yaml
apiVersion: continuity.io/v1
kind: ContinuityPolicy
metadata:
  name: tactical-mission-resilience
  labels:
    classification: "SECRET"
    compartments: ["SOVEREIGN_LOGISTICS", "ARCTIC_NORAD"]
    disseminationControls: ["CANADIAN_EYES_ONLY", "NOFORN"]
    ownerNation: "CAN"
spec:
  targetNetworkId: arctic-defense-resupply
  minimumContinuityScore: 0.95
```

### 3.2 Defense Readiness (DRRS) & C-Level Rule
Declares mandatory defense readiness thresholds evaluated against live supply line states:

```yaml
    - id: DRRS-001
      description: "Unit resupply corridor must maintain at least C-2 Substantially Mission Capable status"
      targetCategory: readiness
      assertion: minimum_drrs_rating
      threshold: "C-2_substantially_capable"
      severity: CRITICAL
```

### 3.3 Electronic Warfare & PNT Spoofing Tolerance Rule
Sets hard limits on acceptable GNSS / PNT signal degradation before automated navigation is marked untrusted:

```yaml
    - id: EW-PNT-002
      description: "PNT telemetry must not exceed 6.0 dB C/N0 drop or 10.0m pseudorange variance"
      targetCategory: navigation
      assertion: max_ew_pnt_degradation
      maxCnoDropDb: 6.0
      maxPseudorangeVarianceM: 10.0
      severity: HIGH
```

---

## 4. CLI Validation & Evaluation

Validate specs against schemas:
```bash
continuity validate examples/arctic/network.yaml
continuity validate examples/arctic/policy.yaml
continuity validate examples/arctic/assurance.yaml
continuity validate examples/arctic/substitution.yaml
```

Run assurance evaluation:
```bash
continuity assurance examples/arctic/assurance.yaml
```

Run substitution compilation:
```bash
continuity substitute examples/arctic/substitution.yaml
```

Run defense readiness and threat audit:
```bash
continuity readiness examples/arctic/assessment.json
continuity threat-scan examples/arctic/telemetry.json
continuity sovereign-audit
```
