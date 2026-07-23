# Key rotation and revocation runbook

Scope: the single-operator reference deployment. This procedure rotates the API key, operator telemetry HMAC secret, and evidence signing key without printing secret values.

## Preparation

1. Confirm the current service and backup state:

```bash
systemctl --user is-active continuityos.service
/home/scott/ai-workspace/repos/continuityos/scripts/status.sh
/home/scott/ai-workspace/repos/continuityos/scripts/backup_data.sh
```

2. Generate replacement material in a private temporary directory. Do not place it in Git, shell history, or chat output.

```bash
umask 077
install -d -m 700 "$HOME/.local/share/continuityos/rotation-$(date +%Y%m%d%H%M%S)"
```

Use the existing CLI/key-generation procedure documented by `python -m continuityos.cli --help`, or generate credentials through the operator's secret manager. The production environment file and key files must remain mode `0600`.

## Rotation order

1. Create the replacement evidence key pair.
2. Back up the current runtime data and environment file.
3. Install the replacement key files.
4. Replace `CONTINUITYOS_API_KEY` and `CONTINUITYOS_OPERATOR_WEBHOOK_SECRET` in `/home/scott/.config/continuityos.env` without echoing values.
5. Restart the user service.
6. Verify the new key with an authenticated read-only request. Verify the old key returns HTTP 401.
7. Verify `/livez`, `/readyz`, `/healthz`, and evidence integrity.
8. Retain the old key only for the documented rollback window, then revoke/destroy it through the secret manager.

## Rollback

If readiness fails, stop using the replacement credentials, restore the backed-up environment and key files, restart the service, and repeat the live checks. Never roll back by copying secrets into the repository.

## Enterprise boundary

For multiple tenants, multiple workers, or strategic/defence procurement, this local procedure is insufficient. Use customer-controlled OIDC, a secret manager, KMS/HSM-backed signing, key versioning, revocation records, dual control, and an audited rotation ceremony. Those are governance and infrastructure decisions, not claims supplied by this repository.
