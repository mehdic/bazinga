---
name: docker
type: infrastructure
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Docker Engineering Expertise

## Specialist Profile
Docker specialist building containerized applications. Expert in multi-stage builds, optimization, and compose configurations.

## Implementation Guidelines

### Multi-Stage Dockerfile

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine AS runner

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

WORKDIR /app

COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./

USER nextjs

EXPOSE 3000
ENV NODE_ENV=production

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "dist/main.js"]
```

### Docker Compose

```yaml
# docker-compose.yml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: runner
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped
    networks:
      - backend

  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: app
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d app"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - backend

volumes:
  postgres_data:
  redis_data:

networks:
  backend:
    driver: bridge
```

### .dockerignore

```
node_modules
npm-debug.log
.git
.gitignore
.env*
!.env.example
Dockerfile*
docker-compose*
.dockerignore
README.md
.vscode
coverage
.nyc_output
dist
```

### Development Compose

```yaml
# docker-compose.dev.yml
services:
  app:
    build:
      context: .
      target: builder
    volumes:
      - .:/app
      - /app/node_modules
    command: npm run dev
    environment:
      - NODE_ENV=development
```

## Patterns to Avoid
- ❌ Running as root
- ❌ Storing secrets in images
- ❌ Using latest tag in production
- ❌ Missing health checks

## Verification Checklist
- [ ] Multi-stage builds
- [ ] Non-root user
- [ ] Health checks defined
- [ ] Proper .dockerignore
- [ ] Volume mounts for persistence
