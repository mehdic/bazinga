---
name: github-actions
type: infrastructure
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# GitHub Actions Engineering Expertise

## Specialist Profile
GitHub Actions specialist building CI/CD pipelines. Expert in workflows, security, and deployment strategies.

---

## Patterns to Follow

### Workflow Structure
- **Concurrency control**: Cancel in-progress on new push
- **Matrix builds**: Test multiple versions in parallel
- **Job dependencies**: Use `needs` for ordering
- **Reusable workflows**: `workflow_call` for DRY
- **Composite actions**: Shared steps as actions

### Caching (Critical for Speed)
- **actions/cache**: NPM, pip, Go modules
- **setup-* actions with cache**: `cache: 'npm'` built-in
- **Docker layer caching**: `cache-from: type=gha`
- **Restore keys**: Fallback to partial cache

### Security Patterns
- **OIDC for cloud auth**: No long-lived credentials
- **Minimal permissions**: `permissions: { }` at workflow level
- **Environment protection**: Required reviewers, wait timers
- **Pin action versions**: `@v4` or SHA for third-party
- **Secret scanning**: Never log secrets

### Deployment Strategies
- **Environment per stage**: dev, staging, production
- **Manual approval**: `environment: production` requires review
- **Rollback capability**: Keep previous artifact/tag
- **Blue/Green or Canary**: Gradual rollout patterns

### Artifact Management
- **Upload for sharing**: Between jobs
- **Retention policy**: Clean up old artifacts
- **Container registry**: Push with git SHA tags
- **Release assets**: Attach binaries to releases

### Performance Optimization
- **Parallel jobs**: Independent steps concurrently
- **Larger runners**: For faster builds (paid)
- **Self-hosted for secrets**: When cloud won't work
- **Early failure**: Fail fast, `fail-fast: true`

### GitHub Actions Features
<!-- version: github-actions >= 2023 -->
- **Required workflows**: Org-level workflow enforcement
- **Larger runners**: 4-64 vCPU options
- **OIDC for all clouds**: AWS, Azure, GCP native
<!-- version: github-actions >= 2024 -->
- **Arm64 runners**: Native ARM builds
- **GPU runners**: ML/AI workloads (beta)
- **Immutable actions**: SHA pinning enforcement
- **Workflow observability**: Built-in insights and metrics

---

## Patterns to Avoid

### Security Anti-Patterns
- ❌ **Secrets in workflow files**: Use secrets/vars
- ❌ **Overly broad permissions**: Default is too permissive
- ❌ **Long-lived cloud credentials**: Use OIDC
- ❌ **Unpinned third-party actions**: Supply chain risk
- ❌ **Echoing secrets**: Even masked, avoid

### Workflow Anti-Patterns
- ❌ **No concurrency limits**: Wasted runners
- ❌ **No caching**: Slow builds
- ❌ **Duplicate steps across workflows**: Use reusable workflows
- ❌ **Hardcoded values**: Use variables
- ❌ **Missing timeout-minutes**: Runaway jobs

### Deployment Anti-Patterns
- ❌ **No environment protection**: Anyone can deploy
- ❌ **Same workflow for all envs**: Use inputs/environments
- ❌ **No rollback plan**: Keep previous versions
- ❌ **Force push main on deploy**: Use tags/releases

### Testing Anti-Patterns
- ❌ **Skipping tests on main**: Always test
- ❌ **No coverage reporting**: Track trends
- ❌ **Tests without artifacts**: Save on failure
- ❌ **Sequential when parallel possible**: Slow feedback

---

## Verification Checklist

### Workflow
- [ ] Concurrency control configured
- [ ] Caching enabled
- [ ] Timeout set
- [ ] Reusable workflows where applicable

### Security
- [ ] OIDC for cloud authentication
- [ ] Minimal permissions declared
- [ ] Actions pinned to versions/SHA
- [ ] Environment protection rules

### Deployment
- [ ] Environment per stage
- [ ] Manual approval for production
- [ ] Rollback strategy documented
- [ ] Artifact retention configured

### Testing
- [ ] Tests run on PR
- [ ] Coverage uploaded
- [ ] Matrix for multiple versions
- [ ] Parallel jobs where possible

---

## Code Patterns (Reference)

### Workflow Structure
- **Concurrency**: `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }`
- **Permissions**: `permissions: { contents: read, id-token: write }`
- **Environment**: `environment: production`

### Caching
- **Node**: `uses: actions/setup-node@v4; with: { node-version: 20, cache: 'npm' }`
- **Docker**: `cache-from: type=gha; cache-to: type=gha,mode=max`

### OIDC (AWS)
- **Configure**: `uses: aws-actions/configure-aws-credentials@v4; with: { role-to-assume: ${{ secrets.AWS_ROLE_ARN }}, aws-region: us-east-1 }`

### Reusable Workflow
- **Call**: `uses: ./.github/workflows/test.yml; with: { node-version: '20' }; secrets: inherit`
- **Define**: `on: workflow_call; inputs: { node-version: { type: string, default: '20' } }`

### Matrix
- **Multiple versions**: `strategy: { matrix: { node: [18, 20, 22] } }; steps: [...setup-node with: node-version: ${{ matrix.node }}]`

