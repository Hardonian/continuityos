# ContinuityOS holistic 50-item closure register

This is the evidence-backed closure register for the reference repository. Status values are deliberately conservative:

- DONE: implemented, tested, and verified in the current deployment.
- VERIFIED-SECURE: inspected and no change was required for this reference scope.
- PARTIAL: a safe local foundation exists, but a production/customer gate remains.
- HUMAN: requires an external account, legal decision, customer data, hardware, or approval.
- DEFERRED: intentionally not added because it would create a second stack or false production signal.

Technical readiness and commercial readiness are separate. A green technical item does not imply a customer, revenue, accreditation, or operational authority.

| # | Layer | Gap / perspective | Status | Evidence or closure condition |
|---:|---|---|---|---|
| 1 | Security | Production configuration must fail closed without signing keys | DONE | `src/continuityos/config.py`; `tests/test_config_cache_ingest.py` |
| 2 | Security | Production API mutations/evidence need an operator credential | DONE | `CONTINUITYOS_API_KEY`; `require_api_key`; live unauthenticated evidence probe returns 401 |
| 3 | Security | Operator telemetry needs authenticated canonical HMAC | VERIFIED-SECURE | `src/continuityos/telemetry.py`; existing signature tests |
| 4 | Security | Evidence needs verifiable Ed25519 signatures | VERIFIED-SECURE | `src/continuityos/evidence.py`; live ledger verification |
| 5 | Security | Secrets must remain outside Git | DONE | runtime env/key paths outside repo; `.env.example` contains placeholders only |
| 6 | Abuse | Request body amplification must be bounded | DONE | `max_request_bytes` middleware; 413 contract |
| 7 | Abuse | Repeated protected requests need throttling | DONE | process-local fixed-window limiter; 429/Retry-After handler |
| 8 | Abuse | Evidence endpoint must not dump unbounded history | DONE | bounded `offset`/`limit` pagination |
| 9 | Abuse | Public OpenAPI can expose production operational surface | DONE | production `openapi_url=None`, docs disabled |
| 10 | Privacy | Error and response metadata need correlation without secrets | DONE | `X-Request-ID`; no credential values in responses |
| 11 | Integrity | Concurrent appenders must not fork the hash chain | DONE | `fcntl` lock file; concurrency test; `ledger.verify()` |
| 12 | Integrity | Evidence writes must be atomic | VERIFIED-SECURE | atomic temporary-file replacement in `evidence.py` |
| 13 | Integrity | Source/metric/assertion mismatches must be rejected | VERIFIED-SECURE | source registry and policy tests |
| 14 | Integrity | Open-data cache must be content-addressed and tamper checked | VERIFIED-SECURE | cache tests including tamper failure |
| 15 | Privacy | Outbound HTTP must be opt-in | VERIFIED-SECURE | default false; live health reports false |
| 16 | Reliability | Health endpoint must detect broken evidence chain | DONE | `/healthz` reports `evidence_ledger_valid`; public probe 200/ok |
| 17 | Reliability | Liveness and readiness semantics need separation | PARTIAL | `/healthz` is safe liveness/integrity; a customer deployment still needs dependency readiness checks |
| 18 | Reliability | Service must bind loopback only | DONE | systemd `127.0.0.1:8082`; `ss` verification |
| 19 | Reliability | Reverse-proxy route must self-repair | DONE | `ensure_caddy_route.py` plus active timer |
| 20 | Reliability | Service startup must be repeatable | DONE | `deploy/continuityos.service`; active after restart |
| 21 | Observability | Requests need minimal metrics | DONE | `/metrics`; counters and duration total |
| 22 | Observability | Edge/application request IDs need propagation | DONE | middleware and live response header |
| 23 | Observability | Logs need stable JSON fields and redaction policy | PARTIAL | uvicorn logs exist; structured shipping/redaction remains for a customer deployment |
| 24 | Observability | Alerts need operator-owned escalation | DEFERRED | reuse lab alerting rather than adding a second notification stack |
| 25 | Data | Runtime data needs an automated backup | DONE | backup service/timer; backup artifact and checksum created |
| 26 | Data | Restore must be explicit and reversible | DONE | `restore_data.sh --confirm` renames current data first |
| 27 | Data | Restore drill must be executed against a disposable copy | DONE | disposable backup/restore drill passed with checksum and reversible rename |
| 28 | Data | Off-host backup/retention needs a separate trust domain | HUMAN | choose encrypted remote target and retention policy |
| 29 | Data | Schema versioning/migrations need governance | PARTIAL | JSON/domain contracts are validated; persistent transactional schema is intentionally absent |
| 30 | Data | Large evidence history needs an indexed store | DEFERRED | SQLite/Postgres would be a new stateful stack; required before customer scale |
| 31 | Delivery | Install/update must be idempotent | DONE | `scripts/install.sh`; systemd unit installation path |
| 32 | Delivery | Status must be inspectable without reading unit files | DONE | `scripts/status.sh` |
| 33 | Delivery | CI must lint, type-check, test, and build | DONE | `.github/workflows/ci.yml`; latest GitHub run passed |
| 34 | Delivery | Dependencies must be reproducible | DONE | pinned `pyproject.toml`, `requirements.pinned.txt`, `uv.lock` |
| 35 | Delivery | Release verification must be runnable locally | VERIFIED-SECURE | `Makefile`, `scripts/verify_release.sh`, successful local gates |
| 36 | Delivery | Docker image must be independently exercised | DONE | image build and compose health/protected-route smoke passed |
| 37 | Delivery | Container secret/key bootstrap must be documented | DONE | `scripts/docker_bootstrap.sh` plus compose init container copies keys with non-root runtime permissions |
| 38 | API | Validation errors must remain 4xx, not hard 500s | VERIFIED-SECURE | API tests cover empty assessment and policy failures |
| 39 | API | API surface needs explicit versioning and bounded models | VERIFIED-SECURE | `/v1` routes and Pydantic domain models |
| 40 | API | API needs customer authentication/authorization and audit roles | PARTIAL | single operator API key is live; RBAC is not claimed |
| 41 | API | Multi-tenant isolation must be enforced | DEFERRED | requires customer identity, tenant model, RLS, and transactional storage |
| 42 | API | Idempotency keys for repeated mutation requests | PARTIAL | evidence IDs are unique; request-level idempotency is still needed before billing/customer use |
| 43 | API | CORS/browser policy needs customer-specific configuration | VERIFIED-SECURE | no permissive CORS added; browser console is not a supported client |
| 44 | Safety | Human approval boundary must remain explicit | VERIFIED-SECURE | compiler emits approval requirement; service does not execute actions |
| 45 | Safety | Domain claims need calibration against real outcomes | HUMAN | requires customer-labeled data and validation protocol |
| 46 | Security | Key rotation and revocation need an operator runbook | PARTIAL | external env/key paths are established; rotation automation is not added |
| 47 | Security | HSM/KMS-backed signing needs an enterprise boundary | DEFERRED | hardware/cloud trust decision required; local Ed25519 is correct for reference scope |
| 48 | Product | Customer onboarding/demo needs a safe seeded workflow | PARTIAL | examples/demo exist; customer-specific onboarding and access issuance remain |
| 49 | Product | Commercial offer needs buyer proof, pricing, and procurement pack | HUMAN | cannot be truthfully generated without target customer validation and legal review |
| 50 | Governance | Security accreditation, privacy, licensing, export, and liability review | HUMAN | external legal/procurement/security decision; never represented as complete by code |

## Highest-leverage next gates

1. Choose a real target operator and validate one corridor with customer-owned observations.
2. Add customer identity/tenant boundaries before storing customer data.
3. Move evidence history to a transactional/indexed store only when the first real workload requires it.
4. Execute a disposable restore drill and select an encrypted off-host backup target.
5. Create a procurement/security pack from real deployment evidence, not claims.
