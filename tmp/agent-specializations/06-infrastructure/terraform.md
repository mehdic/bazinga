---
name: terraform
type: infrastructure
priority: 2
token_estimate: 450
compatible_with: [developer, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Terraform Engineering Expertise

## Specialist Profile
Terraform specialist building infrastructure as code. Expert in modules, state management, and cloud provider patterns.

## Implementation Guidelines

### Module Structure

```hcl
# modules/api/main.tf
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_ecs_service" "api" {
  name            = "${var.environment}-api"
  cluster         = var.cluster_arn
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 3000
  }

  lifecycle {
    ignore_changes = [desired_count]
  }

  tags = var.tags
}
```

### Variables & Outputs

```hcl
# modules/api/variables.tf
variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "cluster_arn" {
  type        = string
  description = "ECS cluster ARN"
}

variable "desired_count" {
  type        = number
  default     = 2
  description = "Number of tasks to run"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags to apply to resources"
}

# modules/api/outputs.tf
output "service_name" {
  value       = aws_ecs_service.api.name
  description = "ECS service name"
}

output "target_group_arn" {
  value       = aws_lb_target_group.api.arn
  description = "Target group ARN for the API"
}
```

### Root Configuration

```hcl
# environments/prod/main.tf
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "prod/api/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Environment = "prod"
      ManagedBy   = "terraform"
      Project     = "api"
    }
  }
}

module "api" {
  source = "../../modules/api"

  environment        = "prod"
  cluster_arn        = data.aws_ecs_cluster.main.arn
  private_subnet_ids = data.aws_subnets.private.ids
  desired_count      = 3

  tags = {
    Team = "platform"
  }
}
```

### Data Sources

```hcl
data "aws_ecs_cluster" "main" {
  cluster_name = "${var.environment}-cluster"
}

data "aws_subnets" "private" {
  filter {
    name   = "tag:Type"
    values = ["private"]
  }
}

data "aws_secretsmanager_secret_version" "db" {
  secret_id = "${var.environment}/database"
}
```

## Patterns to Avoid
- ❌ Hardcoded values (use variables)
- ❌ Local state in production
- ❌ Missing state locking
- ❌ Secrets in state files

## Verification Checklist
- [ ] Remote state with locking
- [ ] Modular structure
- [ ] Variable validation
- [ ] Consistent tagging
- [ ] terraform fmt/validate passes
