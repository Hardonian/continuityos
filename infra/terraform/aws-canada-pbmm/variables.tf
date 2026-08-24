variable "aws_region" {
  description = "Canadian sovereign AWS region strictly within national borders."
  type        = string
  default     = "ca-central-1"
  validation {
    condition     = contains(["ca-central-1", "ca-west-1"], var.aws_region)
    error_message = "Deployment must reside exclusively in a Canadian AWS region (ca-central-1 or ca-west-1) to satisfy PBMM data residency."
  }
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod-sovereign"
}

variable "vpc_cidr" {
  description = "Sovereign VPC IP address block."
  type        = string
  default     = "10.100.0.0/16"
}

variable "enable_guardduty" {
  description = "Enable AWS GuardDuty for continuous threat detection."
  type        = bool
  default     = true
}

variable "enable_waf" {
  description = "Enable AWS WAF v2 with rate limiting and managed rules."
  type        = bool
  default     = true
}

variable "db_instance_class" {
  description = "RDS PostgreSQL instance class."
  type        = string
  default     = "db.r6g.xlarge"
}
