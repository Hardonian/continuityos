#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT/infra/terraform"

command -v terraform >/dev/null 2>&1 || {
  printf 'terraform is required\n' >&2
  exit 1
}
command -v docker >/dev/null 2>&1 || {
  printf 'docker is required for compose validation\n' >&2
  exit 1
}

terraform -chdir="$TF_DIR" fmt -check
terraform -chdir="$TF_DIR" init -backend=false -input=false >/tmp/continuityos-terraform-init.log
terraform -chdir="$TF_DIR" validate
terraform -chdir="$TF_DIR" plan -input=false -lock=false -out=/tmp/continuityos.tfplan >/tmp/continuityos-terraform-plan.log
terraform -chdir="$TF_DIR" show -no-color /tmp/continuityos.tfplan >/tmp/continuityos-terraform-show.log

docker compose -f "$ROOT/docker-compose.yml" config -q
bash -n "$ROOT/scripts/install.sh" "$ROOT/scripts/backup_data.sh" "$ROOT/scripts/restore_data.sh" "$ROOT/scripts/status.sh"

printf 'iac=valid\n'
printf 'terraform_plan=/tmp/continuityos-terraform-show.log\n'
printf 'compose=valid\n'
printf 'shell=valid\n'
