# ContinuityOS Operations Runbook — 2026-07-23

This runbook is an operational template for a controlled pilot/reference deployment. It is not an accreditation, emergency-management authority, or national-security authorization.

## Normal status

```bash
cd /home/scott/ai-workspace/repos/continuityos
scripts/status.sh
make doctor
scripts/drift_check.sh
systemctl --user --no-pager status continuityos.service continuityos-backup.timer
```

Expected:

- `continuityos.service` active.
- `127.0.0.1:8082` is the only ContinuityOS listener.
- `/livez`, `/readyz`, and `/healthz` return 200.
- Anonymous protected routes return 401.
- Backup timer is active.
- Doctor and drift check report zero failures.

## Change procedure

1. Create a branch and record the change reason, owner, risk, rollback commit, and affected data paths.
2. Run `make verify`, `uv run gitleaks detect --source . --no-banner --redact --config .gitleaks.toml`, and `git diff --check`.
3. Review the staged diff for secrets, public listeners, outbound connectivity, auth changes, and tenant-boundary changes.
4. Create a backup with `scripts/backup_data.sh` and verify it with `scripts/verify_backup.sh BACKUP.tar.gz`.
5. Apply only through the reviewed user unit/deployment procedure.
6. Restart the service and run `make doctor`, `scripts/drift_check.sh`, and the public HTTPS smoke checks.
7. Record commit, package hashes, runtime PID, test result, and CI URL in `RELEASE_REPORT.md`.

## Incident procedure

1. If integrity, auth, provenance, or unexpected outbound behavior is suspected, stop public exposure at the approved Caddy/Cloudflare control point; do not delete evidence.
2. Preserve `journalctl --user -u continuityos.service`, the doctor report, the relevant request IDs, and a checksum of the data directory.
3. Disable the user service only if required to contain damage:

```bash
systemctl --user stop continuityos.service
```

4. Do not rotate/delete keys until evidence retention and incident ownership are established.
5. Restore the last verified backup only with an explicit change/incident record:

```bash
scripts/restore_data.sh --confirm /path/to/verified/continuityos-*.tar.gz
systemctl --user restart continuityos.service
make doctor
```

6. If the issue involves root-owned listeners, Kubernetes, SSH, UFW, Caddy, or Cloudflare, escalate to the host owner; do not improvise a root change from the application runbook.

## Backup and recovery

- Local backup timer: `continuityos-backup.timer`.
- Backup directory: `/home/scott/.local/share/continuityos/backups`.
- Retention currently removes archives older than 14 days.
- Each archive has a SHA-256 sidecar and is checked for safe paths before disposable extraction.
- `scripts/verify_backup.sh` performs checksum, traversal, extraction, ledger, and state checks.
- Off-host encrypted backup, restore-site testing, RPO/RTO acceptance, and disaster-recovery ownership remain required governance items.

## Data and security boundaries

- Evidence ledger is append-only and signed locally.
- Export routes are read-only and authenticated.
- Outbound public-data acquisition is disabled by default.
- CloudEvents and CAP are inbound-only; they cannot authorize operational action.
- No customer, government, defence, emergency-management, SCADA, fleet, or classified integration is implied by local endpoints.

## Required approvals before mission-critical use

- Named service owner and on-call owner.
- Security threat model and independent security review.
- Host/root hardening and exposure inventory.
- Backup/restore and disaster-recovery acceptance.
- Legal/privacy/data-retention/cross-border review.
- Customer data-sharing and RBAC authorization.
- Incident response, change control, audit retention, and rollback authority.
- Formal authorization for any government, defence, emergency-management, or national mission use.
