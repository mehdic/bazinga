---
name: terraform
type: infrastructure
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Terraform Engineering Expertise

## Specialist Profile
Terraform specialist building infrastructure as code. Expert in modules, state management, and multi-cloud patterns.

---

## Patterns to Follow

### Module Design
- **Small, focused modules**: Network, compute, database separate
- **Pin versions**: `~> 1.2.0` for providers and modules
- **README with examples**: Usage, inputs, outputs documented
- **Validation rules**: `validation { condition = ... }`
- **Consistent naming**: `${var.environment}-${var.name}`

### State Management
- **Remote backend**: S3, Azure Blob, GCS, Terraform Cloud
- **State locking**: DynamoDB for S3, built-in for cloud backends
- **Encryption at rest**: Enable on backend storage
- **State per environment**: Separate state files for isolation
- **Never edit state manually**: Use `terraform state` commands

### Environment Separation
- **Directory per environment**: `environments/{dev,staging,prod}/`
- **Workspaces for small teams**: But directories provide more isolation
- **Variables per environment**: `terraform.tfvars` per env
- **Different backends per env**: Separate blast radius

### Secret Management
- **Never hardcode secrets**: Use variables marked sensitive
- **External secret stores**: AWS Secrets Manager, Vault, SSM
- **sensitive = true**: Redact from output
- **No secrets in state**: Use data sources to fetch at apply

### CI/CD Integration
- **terraform fmt in CI**: Enforce formatting
- **terraform validate**: Syntax and type checking
- **terraform plan output**: Review before apply
- **Policy as code**: Sentinel, OPA, Conftest
- **Small blast radius**: Limit scope per workspace/directory

### Terraform Version Features
<!-- version: terraform >= 1.3 -->
- **Optional object attributes**: `optional(type, default)` in variable types
- **Moved blocks**: Refactor without destroy/recreate
<!-- version: terraform >= 1.4 -->
- **Null resource replacement**: `terraform_data` resource
- **Cloud variable sets**: Share variables across workspaces
<!-- version: terraform >= 1.5 -->
- **Import blocks**: Declarative import in config
- **Check blocks**: Custom validation conditions
<!-- version: terraform >= 1.6 -->
- **Test framework**: Built-in testing with `terraform test`
<!-- version: terraform >= 1.7 -->
- **Removed blocks**: Declarative resource removal
- **State encryption**: Enhanced state security

### Drift Detection
- **Regular plan runs**: Detect manual changes
- **Automated remediation**: CI job to apply corrections
- **State refresh**: `terraform refresh` (now in plan by default)
- **Import existing resources**: `terraform import`

---

## Patterns to Avoid

### State Anti-Patterns
- ❌ **Local state in production**: No locking, no sharing
- ❌ **Missing state locking**: Concurrent modification corruption
- ❌ **Secrets in state**: Use external secret stores
- ❌ **Monolithic state**: Split by concern/team

### Module Anti-Patterns
- ❌ **Monolithic modules**: Hard to maintain, slow
- ❌ **Unpinned versions**: Breaking changes on update
- ❌ **Missing documentation**: README required
- ❌ **Hardcoded values**: Use variables

### Code Anti-Patterns
- ❌ **Hardcoded credentials**: Use environment variables
- ❌ **No variable validation**: Invalid inputs at runtime
- ❌ **count for conditional**: Use for_each when possible
- ❌ **Missing lifecycle rules**: Prevent accidental destruction

### Workflow Anti-Patterns
- ❌ **apply without plan review**: Dangerous changes
- ❌ **No CI/CD**: Manual applies are error-prone
- ❌ **Skipping terraform fmt**: Inconsistent formatting
- ❌ **One state for all envs**: Blast radius too large

---

## Verification Checklist

### State
- [ ] Remote backend configured
- [ ] State locking enabled
- [ ] Encryption at rest
- [ ] Separate state per environment

### Modules
- [ ] Semantic versioning
- [ ] README with examples
- [ ] Input validation
- [ ] Output documentation

### Security
- [ ] No hardcoded secrets
- [ ] sensitive = true on secrets
- [ ] External secret management
- [ ] IAM least privilege

### CI/CD
- [ ] fmt/validate in pipeline
- [ ] Plan output for review
- [ ] Protected apply step
- [ ] Drift detection scheduled

---

## Code Patterns (Reference)

### Backend
- **S3**: `backend "s3" { bucket = "...", key = "env/terraform.tfstate", region = "...", encrypt = true, dynamodb_table = "tf-locks" }`
- **Terraform Cloud**: `cloud { organization = "..." workspaces { name = "..." } }`

### Variables
- **With validation**: `variable "env" { type = string; validation { condition = contains(["dev","prod"], var.env) } }`
- **Sensitive**: `variable "db_password" { type = string; sensitive = true }`

### Module Call
- **Pinned version**: `module "vpc" { source = "terraform-aws-modules/vpc/aws"; version = "~> 5.0" }`
- **Local module**: `source = "../../modules/api"`

### Lifecycle
- **Prevent destroy**: `lifecycle { prevent_destroy = true }`
- **Ignore changes**: `lifecycle { ignore_changes = [tags] }`
- **Create before destroy**: `lifecycle { create_before_destroy = true }`

### Data Sources
- **Secrets**: `data "aws_secretsmanager_secret_version" "db" { secret_id = "..." }`
- **Remote state**: `data "terraform_remote_state" "vpc" { backend = "s3"; config = {...} }`

