# Aegis ContinuityOS — Security Policy & Coordinated Vulnerability Disclosure

**ContinuityOS** (Continuity-as-Code / Resilience-as-Code) is engineered for defensive resilience modeling, critical infrastructure continuity, and disaster recovery assurance in sovereign, air-gapped, and enterprise enclaves.

---

## 1. Defensive-Only Boundary & Operational Rules of Engagement

ContinuityOS enforces strict defensive boundaries:
- **No Offensive Capabilities**: The system strictly prohibits and will reject features for offensive cyber operations, weapon targeting, kinetic payload routing, interdiction, or sabotage planning.
- **Advisory Boundary**: All plan compilations, route substitutions, and remediation suggestions are strictly advisory. Human-in-the-loop validation is required before executing operational decisions.
- **Air-Gapped Operation**: ContinuityOS core contains zero cloud phone-home mechanisms, no unauthenticated telemetry, and is 100% executable offline without external network access.

---

## 2. Supported Versions

Only the current major release branch receives security patches and vulnerability fixes.

| Version | Supported | Security Updates |
| :--- | :---: | :--- |
| `1.0.x` | **YES** | Active maintenance and security patches |
| `< 1.0.0` | **NO** | End of life; upgrade immediately to v1.0.0 |

---

## 3. Threat Model & Security Posture

### A. Input Deserialization & Parser Hardening
- **YAML & JSON Limits**: File parsing enforces recursion limits, maximum document size thresholds (default: 10MB), and utilizes safe PyYAML / Pydantic schema validation to prevent YAML entity expansion (Billion Laughs) and arbitrary object instantiation.
- **Graph Topology Safety**: Dependency graph construction enforces cycle detection and loop recursion guards (`get_upstream_dependencies` uses visited tracking) to prevent Denial of Service (DoS) via adversarial circular dependencies.

### B. Path Traversal & Shell Injection Mitigation
- CLI commands and file operations use strict cross-platform path normalization (`pathlib.Path.resolve()`) and reject relative path traversal (`../`) out of authorized workspace roots.
- Zero shell invocations: System processes and CLI commands do not invoke untrusted shell interpolation (`shell=False` everywhere).

### C. Cryptographic Provenance & Evidence Integrity
- All observation telemetry and assessment ledgers maintain cryptographic integrity using SHA-256 hash chains.
- Ledger entries support optional asymmetric digital signatures via Ed25519 or Post-Quantum ML-DSA keys.
- Secret handling enforces memory cleansing where available and warns if plaintext credentials are detected in configuration files.

---

## 4. Reporting a Vulnerability

We welcome responsible security research and coordinated disclosure.

### How to Report
1. **Do NOT open a public GitHub issue** for undisclosed security vulnerabilities.
2. Email the vulnerability report privately to: **`security@continuity.io`** (or open a private GitHub Security Advisory).
3. If reporting sensitive sovereign or defense-related vulnerabilities, request our PGP public key prior to sending raw attachments.

### Report Contents
Please include in your advisory:
- Detailed description of the vulnerability and attack vector.
- Minimal reproducible proof-of-concept (PoC) or script.
- Affected components, CLI commands, or DSL resources.
- Remediation suggestions or patches (if developed).

### Response Timeline
- **Initial Acknowledgment**: Within 48 hours.
- **Triage & Reproduction**: Within 5 business days.
- **Patch Development & CVE Assignment**: Within 30 days of confirmed reproduction.
- **Public Disclosure**: Coordinated upon release of the patched version.
