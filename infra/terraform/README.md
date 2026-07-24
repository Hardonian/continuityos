# ContinuityOS local IaC

This module is the local production deployment source of truth for the current EPYC reference deployment.

It intentionally uses Terraform's built-in `terraform_data` resource and no external provider. That keeps the plan reproducible on a machine with Terraform but without cloud credentials, a provider registry dependency, or an invented Kubernetes/cloud target.

## Default safety behavior

The default is plan-only:

```bash
terraform -chdir=infra/terraform init -backend=false
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
terraform -chdir=infra/terraform plan
```

No systemd unit, data directory, service, or Caddy route is changed by the default plan.

## Apply the local deployment explicitly

Prerequisites:

- `/home/scott/.config/continuityos.env` exists and is mode `600`;
- the checkout path in `terraform.tfvars` is correct;
- the operator has reviewed the plan;
- `continuityos.service` is the intended user unit.

Apply:

```bash
terraform -chdir=infra/terraform apply \
  -var='apply_local=true' \
  -auto-approve
```

The apply synchronizes the existing deploy units, creates the runtime/backup directories, reloads the user systemd manager, enables the service and timers, and verifies `ExecMainStatus=0`.

## Rollback

Terraform rollback is deliberately conservative. It does not delete the data directory or destroy evidence keys.

1. Stop the service:

```bash
systemctl --user disable --now continuityos.service
```

2. Restore the prior application commit:

```bash
git -C /home/scott/ai-workspace/repos/continuityos checkout <known-good-commit>
```

3. Re-run the install or Terraform apply against that commit.

4. Restore data only with explicit confirmation:

```bash
bash scripts/restore_data.sh --confirm /path/to/continuityos-YYYYmmddTHHMMSSZ.tar.gz
```

5. Verify the service and evidence ledger before re-exposing the route.

## Design boundary

This module does not claim to provision:

- Cloudflare DNS or Tunnel resources;
- Caddy root-owned configuration;
- customer identity providers;
- customer GIS/SIEM/SensorThings endpoints;
- Kafka, NATS, MQTT, or Redis;
- Kubernetes or cloud databases;
- HSM/KMS keys.

Those require a named target, credentials, authorization, and a separate verified module. The next cloud/IaC module should be written only after selecting the actual target account and state backend.
