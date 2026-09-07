# ContinuityOS v1.0 — Demo Script & Walkthrough

This script guides an evaluator through an interactive 5-to-8 minute terminal demonstration of **ContinuityOS** executing against actual local code.

No internet connectivity, cloud APIs, or mocked terminal outputs are used. Every step evaluates declarative schemas, runs deterministic algorithms, and reconciles state.

---

## Prerequisites

```bash
git clone https://github.com/continuityos/continuityos.git
cd continuityos
uv sync --all-extras
```

Run the automated demonstration runner directly:

```bash
continuity demo arctic
# or civilian reference implementation:
continuity demo civilian
```

---

## Step-by-Step Interactive Walkthrough

### 1. Inspect Declared Continuity Objectives
Explain: *"Like Terraform or Kubernetes, ContinuityOS starts with a declared desired state. Here is our critical maritime supply policy."*

```bash
cat examples/arctic/network.yaml
cat examples/arctic/policy.yaml
```

**Key Observation**: The policy declares:
- Minimum continuity objective $\ge 95\%$
- Minimum 2 independent communication providers
- Fuel reserve buffer $\ge 30\text{ days}$
- Zero single-state service dependencies

---

### 2. Validate Policy Specifications
Explain: *"Continuity-as-Code files are strictly validated against machine-readable JSON schemas before deployment."*

```bash
continuity validate examples/arctic/network.yaml
continuity validate examples/arctic/policy.yaml
```

**Output**:
```json
{
  "valid": true,
  "resources_checked": 1,
  "errors": []
}
```

---

### 3. Observe Pre-Disruption Baseline Plan
Explain: *"Under nominal conditions, our primary supply corridor (Northern Sea Route) is open and insured."*

```bash
continuity plan examples/arctic/network.yaml
```

**Output**:
- Declared continuity: 95.0%
- Observed continuity: 98.2%
- Status: **COMPLIANT**

---

### 4. Inject Correlated Disruption Event
Explain: *"Traditional risk software assumes disruptions are independent. In reality, disasters and geopolitical crises cascade across multiple layers simultaneously."*

Inject:
1. Marine war-risk underwriters withdraw coverage at Lloyd's of London.
2. Polar vortex / pressure ridge pack closure.
3. Commercial LEO constellation experiences geomagnetic space weather blackout.

```bash
continuity simulate examples/arctic/scenario.yaml
```

---

### 5. Prove Invariant 1: Physical Open != Effective Open
Explain: *"A satellite radar image shows the waterway is physically navigable. Traditional monitoring says 'GREEN / OPEN'. But what is its operational reality?"*

```bash
continuity explain corridor/nsr
```

**Output**:
```text
==============================================================================
CONTINUITYOS FUNCTIONAL CLOSURE EXPLANATION TRACE
==============================================================================
Resource:        corridor/nsr
Effective State: OPEN_BUT_UNINSURABLE
Confidence:      85.0%

Four-Layer Decomposition:
  [PHYSICAL]      AVAILABLE    (conf: 0.90)
  [OPERATIONAL]   DEGRADED     (conf: 0.80) -> navigation_untrusted
  [COMMERCIAL]    UNAVAILABLE  (conf: 0.85) -> uninsurable, no_carrier_capacity
  [DIGITAL TRUST] DEGRADED     (conf: 0.75) -> data_integrity_low
  [RECOVERY]      AVAILABLE    (conf: 0.95)

Reason Codes:
  - uninsurable
  - no_carrier_capacity
==============================================================================
```
**Takeaway**: Physical availability is meaningless when commercial insurers and container carriers refuse transit. The route is **FUNCTIONALLY CLOSED**.

---

### 6. Model Strategic Inventory Depletion & Assured Replenishment
Explain: *"With the primary route functionally closed, how long do emergency operations survive before reserve exhaustion? And when can replenishment actually arrive?"*

```bash
continuity inventory examples/arctic/network.yaml
```

**Output**:
- Normal burn: 1,200 units/day
- Degraded burn: 1,800 units/day
- **Days to Warning**: Day 16
- **Days to Critical**: Day 23
- **Days to Exhaustion**: Day 27
- **Assured Replenishment Days**: **45 days**

**Takeaway**: Raw inventory says 27 days of fuel, but next credible replenishment takes 45 days. **Inventory will exhaust 18 days before replenishment arrives.**

---

### 7. Compile Route Substitution: Why Lines on Maps Fail
Explain: *"Other tools draw a line through an alternate route (e.g. Pacific transshipment). ContinuityOS proves whether the alternate supply chain can actually satisfy continuity objectives."*

```bash
continuity substitute examples/arctic/substitution.yaml
```

**Evaluation 1: Pacific / Transshipment Alternative**:
- Geographically viable: **YES**
- Commercially viable: **YES**
- Port handling capacity: **DEGRADED (Bottleneck)**
- Arrival before critical inventory date: **NO (Arrives Day 36 > Deadline Day 28)**
- Result: **REJECTED**

**Evaluation 2: North Atlantic Corridor via Kirkenes**:
- Geographically viable: **YES** (Ice-class certified)
- Commercially viable: **YES** (Hull insurance active)
- Port handling capacity: **PASS**
- Inland rail fluidity: **PASS**
- Arrival before critical inventory date: **YES (Arrives Day 20 <= Deadline Day 28)**
- Result: **ACCEPTED & ACTIVATED**

---

### 8. Prove Invariant 8: Recovery Lag (T0 -> T5)
Explain: *"When the primary route physically reopens at Day 12, is the network healthy? No! Vessel repositioning, port backlogs, and inventory restoration take weeks."*

```bash
continuity recovery examples/arctic/network.yaml
```

**Output**:
- Day 12: Physical route open (T1) -> `reopened_but_not_healthy = True`
- Day 30: Commercial underwriters return (T2)
- Day 48: Port container backlogs clear (T3)
- Day 88: Strategic inventory replenished (T4)
- Day 94: Full resilience objective restored (T5) -> `is_healthy = True`

---

### 9. Final Closed-Loop Reconciliation
Explain: *"With the Atlantic route substituted and secondary communications activated, the system reconciles back to compliance."*

```bash
continuity drift examples/arctic/network.yaml
```

**Output**:
- Declared continuity: 95.0%
- Observed continuity: 96.5%
- Status: **COMPLIANT**

---

## Conclusion

In under 8 minutes, the evaluator has seen:
1. Declarative resilience policy in Git.
2. Functional closure detection (physical vs. commercial).
3. Correlated disruption cascades.
4. Assured replenishment calculations.
5. Exact route substitution proof.
6. Recovery lag modeling ($T0 \to T5$).
7. Machine-readable audit evidence.
