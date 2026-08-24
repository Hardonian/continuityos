terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project              = "ContinuityOS-Sovereign"
      Environment          = var.environment
      DataClassification   = "PROTECTED_B"
      SecurityProfile      = "ITSG-33-PBMM"
      DataResidencyCountry = "CAN"
    }
  }
}

# 1. Customer Managed Key (CMK) for Envelope Encryption
resource "aws_kms_key" "sovereign_cmk" {
  description             = "ContinuityOS Sovereign CMK for Protected B at-rest encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "continuityos-sovereign-cmk"
  }
}

resource "aws_kms_alias" "sovereign_cmk_alias" {
  name          = "alias/continuityos-sovereign"
  target_key_id = aws_kms_key.sovereign_cmk.key_id
}

# 2. Sovereign VPC & Private Subnets
resource "aws_vpc" "sovereign_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "continuityos-sovereign-vpc"
  }
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.sovereign_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 1)
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "continuityos-private-a"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.sovereign_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 2)
  availability_zone = "${var.aws_region}b"

  tags = {
    Name = "continuityos-private-b"
  }
}

# 3. VPC Flow Logs to Encrypted CloudWatch
resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/aws/vpc/continuityos-sovereign-flow-logs"
  kms_key_id        = aws_kms_key.sovereign_cmk.arn
  retention_in_days = 365
}

resource "aws_flow_log" "vpc_flow" {
  iam_role_arn    = aws_iam_role.flow_log_role.arn
  log_destination = aws_cloudwatch_log_group.flow_logs.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.sovereign_vpc.id
}

resource "aws_iam_role" "flow_log_role" {
  name = "continuityos-flow-log-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "vpc-flow-logs.amazonaws.com"
      }
    }]
  })
}

# 4. Multi-AZ Encrypted RDS PostgreSQL
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "continuityos-rds-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}

resource "aws_db_instance" "sovereign_rds" {
  identifier              = "continuityos-sovereign-db"
  engine                  = "postgres"
  engine_version          = "16.2"
  instance_class          = var.db_instance_class
  allocated_storage       = 100
  max_allocated_storage   = 1000
  storage_type            = "gp3"
  storage_encrypted       = true
  kms_key_id              = aws_kms_key.sovereign_cmk.arn
  multi_az                = true
  db_subnet_group_name    = aws_db_subnet_group.rds_subnet_group.name
  skip_final_snapshot     = false
  final_snapshot_identifier = "continuityos-final-snapshot"
  backup_retention_period = 35
  deletion_protection     = true
  auto_minor_version_upgrade = true
  publicly_accessible     = false
}

# 5. GuardDuty Continuous Threat Detection
resource "aws_guardduty_detector" "primary" {
  count  = var.enable_guardduty ? 1 : 0
  enable = true
}

output "sovereign_residency_summary" {
  value = {
    region                = var.aws_region
    country               = "CAN"
    compliance_baseline   = "ITSG-33 / PBMM"
    kms_cmk_arn           = aws_kms_key.sovereign_cmk.arn
    rds_endpoint          = aws_db_instance.sovereign_rds.endpoint
    vpc_id                = aws_vpc.sovereign_vpc.id
  }
}
