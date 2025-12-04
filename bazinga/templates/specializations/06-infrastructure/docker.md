---
name: docker
type: infrastructure
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Docker Engineering Expertise

## Specialist Profile
Docker specialist building containerized applications. Expert in multi-stage builds, security, and optimization.

---

## Patterns to Follow

### Multi-Stage Builds (50-85% size reduction)
- **Separate build and runtime stages**: Only copy artifacts
- **Name stages for clarity**: `FROM node:20-alpine AS builder`
- **Parallel stages for speed**: Independent builds run concurrently
- **Use --from for specific copies**: `COPY --from=builder /app/dist ./`
- **Minimal runtime images**: Alpine, distroless, scratch

### Layer Optimization
- **Order by change frequency**: Less-changing first (cache hits)
- **Combine RUN commands**: Single layer with `&&`
- **Clean up in same layer**: `apt-get clean && rm -rf /var/lib/apt/lists/*`
- **Use COPY instead of ADD**: More predictable
- **Leverage .dockerignore**: Exclude build artifacts, secrets

### Security (Critical)
- **Run as non-root**: Create user with adduser, use USER directive
- **Distroless for production**: No shell, minimal attack surface
- **Pin base image versions**: Never use :latest in production
- **Scan images**: Trivy, Snyk, Grype in CI
- **No secrets in images**: Use runtime injection

### Base Image Selection
- **Alpine for size**: ~5MB base
- **Distroless for security**: No shell/package manager
- **Debian slim for compatibility**: When Alpine has musl issues
- **Language-specific**: `python:3.12-slim`, `node:20-alpine`

### Health Checks
- **HEALTHCHECK in Dockerfile**: Built-in monitoring
- **Appropriate intervals**: 30s default, adjust per app
- **Start period for slow init**: Avoid false positives
- **CMD or curl/wget**: HTTP or TCP checks

### Compose Best Practices
- **depends_on with condition**: `condition: service_healthy`
- **Named volumes for persistence**: Not bind mounts in prod
- **Networks for isolation**: Separate frontend/backend
- **Environment files**: `.env` for secrets (not committed)

### Docker Build Features
<!-- version: docker >= 23.0 -->
- **BuildKit default**: Parallel builds, cache mounts, secrets
- **--build-context**: Multiple named build contexts
<!-- version: docker >= 24.0 -->
- **Bake file improvements**: Better multi-platform builds
<!-- version: docker >= 25.0 -->
- **Container storage driver**: containerd default integration
<!-- version: compose >= 2.0 -->
- **GPU support**: `deploy.resources.reservations.devices`
- **Profiles**: Selective service startup with `profiles: [dev]`

---

## Patterns to Avoid

### Security Anti-Patterns
- ❌ **Running as root (58% of containers do!)**: Use USER directive
- ❌ **Secrets in images/layers**: Visible in history
- ❌ **Using :latest in production**: Unpredictable
- ❌ **ADD for URLs**: Use curl/wget in RUN for control
- ❌ **Disabling security features**: Keep defaults

### Build Anti-Patterns
- ❌ **Not using multi-stage**: Bloated images
- ❌ **One command per RUN**: Too many layers
- ❌ **Caching package manager last**: Slow rebuilds
- ❌ **Missing .dockerignore**: Large context, secrets leaked
- ❌ **COPY . . before npm install**: Busts cache

### Runtime Anti-Patterns
- ❌ **No health checks**: Unhealthy containers stay running
- ❌ **Logging to files**: Use stdout/stderr
- ❌ **Storing state in container**: Use volumes
- ❌ **Hard-coded environment**: Use env vars

### Compose Anti-Patterns
- ❌ **depends_on without health checks**: Race conditions
- ❌ **Anonymous volumes**: Hard to manage
- ❌ **Secrets in compose file**: Commit risk
- ❌ **Not using networks**: All containers can talk

---

## Verification Checklist

### Build
- [ ] Multi-stage build used
- [ ] Minimal base image selected
- [ ] Layers ordered for caching
- [ ] .dockerignore present

### Security
- [ ] Non-root user (USER directive)
- [ ] Base image version pinned
- [ ] Image scanned in CI
- [ ] No secrets in image

### Runtime
- [ ] HEALTHCHECK defined
- [ ] Logs to stdout/stderr
- [ ] Environment via env vars
- [ ] Volumes for persistence

### Compose
- [ ] Health checks with depends_on
- [ ] Named networks/volumes
- [ ] Secrets not committed
- [ ] restart policy set

---

## Code Patterns (Reference)

### Multi-Stage
- **Builder stage**: `FROM node:20-alpine AS builder; WORKDIR /app; COPY package*.json ./; RUN npm ci; COPY . .; RUN npm run build`
- **Runtime stage**: `FROM node:20-alpine AS runner; COPY --from=builder /app/dist ./dist`

### Non-Root User
- **Create user**: `RUN addgroup --system --gid 1001 app && adduser --system --uid 1001 app`
- **Switch user**: `USER app`

### Health Check
- **HTTP**: `HEALTHCHECK --interval=30s --timeout=3s CMD wget --spider http://localhost:3000/health || exit 1`
- **TCP**: `HEALTHCHECK CMD nc -z localhost 5432 || exit 1`

### Layer Optimization
- **Combine & clean**: `RUN apt-get update && apt-get install -y pkg && apt-get clean && rm -rf /var/lib/apt/lists/*`

### .dockerignore
- **Essential excludes**: `node_modules`, `.git`, `*.md`, `.env*`, `Dockerfile*`, `docker-compose*`

