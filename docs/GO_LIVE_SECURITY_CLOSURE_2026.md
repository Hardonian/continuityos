# ContinuityOS Go-Live Security Closure — 2026-07-23

## Decision

ContinuityOS is technically ready for a controlled reference/pilot deployment behind the existing authenticated Caddy/Cloudflare route. It is not an accredited national-security system and must not be represented as one. It has no classified-data authorization, government endorsement, customer operational authority, or live bidirectional control.

## Verified closed

- Production configuration fails closed when API key, operator secret, or Ed25519 evidence keys are missing.
- API key comparison uses constant-time comparison.
- Evidence, interoperability, export, and catalog routes require the API key.
- Request bodies are bounded; rate limits and request IDs are active.
- Evidence ledger integrity is checked by readiness.
- Outbound HTTP remains disabled by default.
- Local service binds only to `127.0.0.1:8082`.
- User-level systemd sandbox is active with `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=strict`, `ProtectHome=read-only`, `LockPersonality`, `RestrictSUIDSGID`, restrictive `UMask`, and a write exception only for the ContinuityOS data directory.
- The managed systemd PID owns the listener after restart.
- Local `/livez`, `/readyz`, and `/healthz` pass.
- Public `/continuityos/healthz` passes through Cloudflare/Caddy.
- Public protected routes return 401 without credentials.
- Public security headers are present: HSTS, CSP, frame denial, nosniff, referrer policy, permissions policy, and no-store.
- IaC defaults to plan-only and rejects public binds, privileged workloads, host networking, and unignored state.
- Signed CloudEvents and protected CAP ingestion are implemented with idempotency/replay controls.
- GeoJSON, GeoPackage, NDJSON, manifest, and metadata-only STAC exports are implemented.
- Docker runs as non-root and fails closed when production prerequisites are absent.
- 59 tests pass at 86.70% coverage; Ruff, mypy, Gitleaks, package build, IaC, and CI pass.
- Local backup timer exists and restore is reversible/disposable; off-host disaster recovery is not claimed.
- Latest local backup checksum and disposable extraction/ledger/state verification passed; off-host encrypted backup and RPO/RTO acceptance are not claimed.

## Host-level open blocker

The broader EPYC host currently has root-owned MicroK8s/kubelite wildcard listeners including Kubernetes control-plane ports (`16443`, `10250`, `10257`, `10259`, `4369`) and other host-wide listeners. UFW is not active. These are not ContinuityOS listeners, but they prevent a truthful claim of host-wide lockdown.

The agent did not kill, firewall, disable, or modify them because doing so without root ownership confirmation and a maintenance window could break Kubernetes, SSH, Caddy, or unrelated workloads.

Reviewed runbook:

```text
/home/scott/.staged/continuityos-host-exposure-hardening.sh
```

The runbook is audit-only by default and requires explicit root execution with `APPLY=1` for the firewall baseline. It creates timestamped backups and preserves SSH/HTTP/HTTPS/loopback before denying MicroK8s control-plane ports.

## Required before claiming hardened host-wide production

1. Review the staged host runbook.
2. Confirm MicroK8s is required; disable it only if intentionally unused.
3. Verify SSH key access from a second session before enabling UFW.
4. Run the runbook during a maintenance window.
5. Verify `ufw status` reports `Status: active`.
6. Verify Kubernetes/API ports are not reachable from the LAN.
7. Verify Caddy/Cloudflare public route and ContinuityOS health after the change.
8. Confirm all root-owned listeners have an owner, purpose, and exposure decision.
9. Add off-host encrypted backup and perform a restore drill.
10. Obtain formal legal, privacy, security, procurement, accreditation, and customer authorization before any national/mission-critical claim.

## Rollback

- Application: `git revert <release-commit>`; reinstall the prior package; restart `continuityos.service`; verify `/readyz`.
- Data: use `scripts/restore_data.sh --confirm <verified-backup>` after preserving the current data directory.
- Host firewall: use the timestamped backup under `/root/continuityos-host-hardening-*/` only during a reviewed maintenance window.
- Never restore a root firewall/config backup blindly over an active SSH session.
