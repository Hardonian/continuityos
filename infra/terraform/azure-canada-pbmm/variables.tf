variable "azure_location" {
  description = "Canadian sovereign Azure region strictly within national borders."
  type        = string
  default     = "canadacentral"
  validation {
    condition     = contains(["canadacentral", "canadaeast"], var.azure_location)
    error_message = "Azure location must reside strictly in Canada Central (Toronto) or Canada East (Quebec City) for PBMM data residency."
  }
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod-sovereign-azure"
}

variable "resource_group_name" {
  description = "Resource group for sovereign workloads."
  type        = string
  default     = "rg-continuityos-sovereign"
}
