---
name: kubernetes
type: infrastructure
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Kubernetes Engineering Expertise

## Specialist Profile
Kubernetes specialist deploying containerized workloads. Expert in deployments, security, and production-grade patterns.

---

## Patterns to Follow

### Pod & Deployment Patterns
- **Never run naked pods**: Use Deployment, DaemonSet, StatefulSet
- **Pod anti-affinity**: Spread across nodes/zones
- **Resource requests AND limits**: Always set both
- **Probes**: liveness (is alive), readiness (can serve), startup (slow init)
- **Rolling updates**: maxSurge/maxUnavailable for zero-downtime

### Security Patterns (Critical)
- **runAsNonRoot: true**: Never run containers as root
- **seccomp/AppArmor profiles**: Restrict system calls
- **Network policies**: Default deny, explicit allow
- **RBAC**: Least privilege, namespace-scoped roles
- **Image scanning**: Before deployment

### Secrets Management (2025)
- **External Secrets Operator**: Fetch from Vault/AWS/GCP
- **Never commit secrets to Git**: Reference only
- **Sealed Secrets for GitOps**: Encrypted in repo
- **CSI Secret Store**: Mount secrets as volumes
- **Short-lived credentials**: Rotate automatically

### Gateway API (New Standard)
<!-- version: kubernetes >= 1.28 -->
- **Replaces Ingress**: More powerful, standardized
- **HTTPRoute**: Advanced traffic routing
- **GRPCRoute**: Native gRPC support
- **Gateway class**: Infrastructure abstraction
- **Cross-namespace references**: Secure sharing

### GitOps Fleet Management
- **ArgoCD ApplicationSets**: Template-based multi-cluster
- **Flux**: Auto-reconciliation from Git
- **Immutable upgrades (Blue/Green)**: Safest upgrade method
- **Drift detection**: Automated remediation

### Version Policy
- **Max 2 versions behind**: Security patches, avoid big jumps
- **Cluster API for upgrades**: Declarative cluster management
- **Test in staging first**: Never upgrade prod blindly

---

## Patterns to Avoid

### Security Anti-Patterns
- ❌ **Running as root**: Security risk, container escape
- ❌ **Committing secrets to Git**: Even encrypted is risky
- ❌ **No network policies**: All pods can talk to all
- ❌ **privileged: true**: Full host access
- ❌ **Missing RBAC**: Default service accounts

### Resource Anti-Patterns
- ❌ **No resource limits**: Node exhaustion, noisy neighbors
- ❌ **Limits without requests**: Scheduler can't optimize
- ❌ **CPU limits too low**: Throttling, performance issues
- ❌ **Missing PodDisruptionBudget**: Unsafe maintenance

### Deployment Anti-Patterns
- ❌ **Using :latest tag**: Unpredictable deployments
- ❌ **No health probes**: Unhealthy pods receive traffic
- ❌ **Single replica without reason**: No HA
- ❌ **Ignoring init containers**: Race conditions
- ❌ **Large monolithic Helm charts**: Split by concern

### Operational Anti-Patterns
- ❌ **More than 2 versions behind**: Security risk
- ❌ **No HPA for variable load**: Over/under provisioned
- ❌ **Ingress instead of Gateway API**: Legacy pattern
- ❌ **Local kubectl apply to prod**: Use GitOps

---

## Verification Checklist

### Security
- [ ] runAsNonRoot in security context
- [ ] Network policies in place
- [ ] Secrets via External Secrets Operator
- [ ] RBAC roles are namespace-scoped
- [ ] Image scanning in CI

### Resources
- [ ] Requests and limits set
- [ ] HPA configured for scaling
- [ ] PodDisruptionBudget defined
- [ ] Anti-affinity for HA

### Deployments
- [ ] All three probe types configured
- [ ] Rolling update strategy defined
- [ ] Image tags pinned (not :latest)
- [ ] ConfigMaps/Secrets mounted properly

### Operations
- [ ] GitOps deployment (ArgoCD/Flux)
- [ ] Monitoring and alerting
- [ ] Cluster within 2 versions of latest
- [ ] Disaster recovery tested

---

## Code Patterns (Reference)

### Security Context
- **Pod level**: `securityContext: { runAsNonRoot: true, runAsUser: 1000, fsGroup: 1000 }`
- **Container level**: `securityContext: { allowPrivilegeEscalation: false, readOnlyRootFilesystem: true }`

### Resources
- **Requests/Limits**: `resources: { requests: { cpu: "100m", memory: "128Mi" }, limits: { cpu: "500m", memory: "512Mi" } }`

### Probes
- **Liveness**: `livenessProbe: { httpGet: { path: /health, port: 3000 }, initialDelaySeconds: 10 }`
- **Readiness**: `readinessProbe: { httpGet: { path: /ready, port: 3000 }, periodSeconds: 5 }`

### Anti-Affinity
- **Pod**: `podAntiAffinity: { preferredDuringSchedulingIgnoredDuringExecution: [...] }`

### Network Policy
- **Deny all**: `spec: { podSelector: {}, policyTypes: [Ingress, Egress] }` (no ingress/egress rules = deny)

