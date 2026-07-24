terraform {
  required_version = ">= 1.4.0"
}

variable "apply_local" {
  description = "When true, synchronize the user systemd units and runtime directories. Defaults to plan-only."
  type        = bool
  default     = false
}

variable "repo_root" {
  description = "Absolute ContinuityOS checkout used by the local deployment."
  type        = string
  default     = "/home/scott/ai-workspace/repos/continuityos"
}

variable "data_dir" {
  description = "Persistent application data directory."
  type        = string
  default     = "/home/scott/.local/share/continuityos"
}

variable "env_file" {
  description = "Mode-600 runtime environment file outside Git."
  type        = string
  default     = "/home/scott/.config/continuityos.env"
}

variable "service_port" {
  description = "Loopback-only systemd service port."
  type        = number
  default     = 8082
  validation {
    condition     = var.service_port >= 1024 && var.service_port <= 65535
    error_message = "service_port must be an unprivileged TCP port."
  }
}

variable "enable_backup_timer" {
  description = "Install and enable the existing daily backup timer when apply_local is true."
  type        = bool
  default     = true
}

locals {
  user_unit_dir = pathexpand("~/.config/systemd/user")
  unit_names = concat(
    ["continuityos.service", "continuityos-caddy-route.service"],
    var.enable_backup_timer ? ["continuityos-backup.service"] : [],
  )
  timer_names = concat(
    ["continuityos-caddy-route.timer"],
    var.enable_backup_timer ? ["continuityos-backup.timer"] : [],
  )
  desired_files = concat(local.unit_names, local.timer_names)
}

resource "terraform_data" "local_deployment" {
  count = var.apply_local ? 1 : 0

  triggers_replace = concat(
    [
      var.repo_root,
      var.data_dir,
      var.env_file,
      tostring(var.service_port),
    ],
    [
      for file_name in local.desired_files : filesha256("${var.repo_root}/deploy/${file_name}")
    ],
  )

  provisioner "local-exec" {
    interpreter = ["/usr/bin/env", "bash", "-c"]
    command     = <<-EOT
      set -Eeuo pipefail
      test -d "${var.repo_root}"
      test -r "${var.env_file}"
      test "$(stat -c '%a' "${var.env_file}")" = "600"
      install -d -m 700 "${local.user_unit_dir}"
      install -d -m 700 "${var.data_dir}"
      install -d -m 700 "${var.data_dir}/backups"
      %{for file_name in local.desired_files~}
      install -m 0644 "${var.repo_root}/deploy/${file_name}" "${local.user_unit_dir}/${file_name}"
      %{endfor~}
      systemctl --user daemon-reload
      systemctl --user enable --now continuityos.service
      systemctl --user enable --now continuityos-caddy-route.timer
      %{if var.enable_backup_timer~}
      systemctl --user enable --now continuityos-backup.timer
      %{endif~}
      systemctl --user is-active continuityos.service
      test "$(systemctl --user show continuityos.service -p ExecMainStatus --value)" = "0"
    EOT
  }
}

output "deployment_mode" {
  value = var.apply_local ? "apply-local" : "plan-only"
}

output "service" {
  value = {
    bind     = "127.0.0.1:${var.service_port}"
    unit     = "continuityos.service"
    data_dir = var.data_dir
    env_file = var.env_file
    unit_dir = local.user_unit_dir
    backup   = var.enable_backup_timer
  }
}

output "verification_commands" {
  value = [
    "systemctl --user is-active continuityos.service",
    "systemctl --user show continuityos.service -p MainPID -p ExecMainStatus",
    "curl --fail http://127.0.0.1:${var.service_port}/readyz",
    "bash ${var.repo_root}/scripts/status.sh",
    "bash ${var.repo_root}/scripts/backup_data.sh",
  ]
}
