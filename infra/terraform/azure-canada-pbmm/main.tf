terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
  }
}

# 1. Resource Group
resource "azurerm_resource_group" "sovereign_rg" {
  name     = var.resource_group_name
  location = var.azure_location

  tags = {
    Environment        = var.environment
    DataClassification = "PROTECTED_B"
    SecurityProfile    = "ITSG-33-PBMM"
    Country            = "CAN"
  }
}

# 2. Key Vault with HSM / CMK
data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "sovereign_kv" {
  name                        = "kv-continuityos-sov"
  location                    = azurerm_resource_group.sovereign_rg.location
  resource_group_name         = azurerm_resource_group.sovereign_rg.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 90
  purge_protection_enabled    = true
  sku_name                    = "premium" # FIPS 140-2 Level 3 HSM support

  network_acls {
    bypass         = "AzureServices"
    default_action = "Deny"
  }
}

# 3. Azure Virtual Network & Subnets
resource "azurerm_virtual_network" "sovereign_vnet" {
  name                = "vnet-continuityos-sovereign"
  address_space       = ["10.200.0.0/16"]
  location            = azurerm_resource_group.sovereign_rg.location
  resource_group_name = azurerm_resource_group.sovereign_rg.name
}

resource "azurerm_subnet" "app_subnet" {
  name                 = "snet-continuityos-app"
  resource_group_name  = azurerm_resource_group.sovereign_rg.name
  virtual_network_name = azurerm_virtual_network.sovereign_vnet.name
  address_prefixes     = ["10.200.1.0/24"]
}

output "azure_sovereignty_summary" {
  value = {
    location             = var.azure_location
    resource_group       = azurerm_resource_group.sovereign_rg.name
    key_vault_uri        = azurerm_key_vault.sovereign_kv.vault_uri
    compliance_baseline  = "CCCS ITSG-33 / PBMM"
    data_residency       = "Canada Central (Toronto)"
  }
}
