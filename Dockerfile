# BAZINGA CLI Docker Image
#
# Multi-stage build for a minimal production image
# Supports both amd64 and arm64 architectures
#
# Build:
#   docker build -t bazinga-cli .
#
# Run:
#   docker run -it --rm -v $(pwd):/project bazinga-cli init --here
#
# With offline mode:
#   docker run -it --rm -v $(pwd):/project bazinga-cli init --here --offline

# ============================================================================
# Stage 1: Build stage
# ============================================================================
FROM python:3.11-slim as builder

# Build arguments
ARG VERSION=dev

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /build

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
COPY agents/ ./agents/
COPY templates/ ./templates/
COPY workflow/ ./workflow/
COPY scripts/ ./scripts/
COPY .claude/ ./.claude/
COPY bazinga/ ./bazinga/
COPY dashboard-v2/ ./dashboard-v2/
COPY mini-dashboard/ ./mini-dashboard/

# Build the wheel
RUN pip install --upgrade pip hatch && \
    hatch build && \
    ls -la dist/

# ============================================================================
# Stage 2: Production image
# ============================================================================
FROM python:3.11-slim as production

# Labels for container metadata
LABEL org.opencontainers.image.title="BAZINGA CLI" \
      org.opencontainers.image.description="Multi-Agent Orchestration System for Claude Code" \
      org.opencontainers.image.url="https://github.com/mehdic/bazinga" \
      org.opencontainers.image.source="https://github.com/mehdic/bazinga" \
      org.opencontainers.image.vendor="Mehdi C" \
      org.opencontainers.image.licenses="MIT"

# Build arguments
ARG VERSION=dev
ENV BAZINGA_VERSION=${VERSION}

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Default to offline mode in containers (no network assumptions)
    BAZINGA_OFFLINE=0

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    # For dashboard (optional)
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g npm@latest

# Create non-root user for security
RUN groupadd --gid 1000 bazinga && \
    useradd --uid 1000 --gid bazinga --shell /bin/bash --create-home bazinga

# Copy wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/

# Install BAZINGA CLI
RUN pip install /tmp/*.whl && \
    rm -rf /tmp/*.whl

# Create project mount point
RUN mkdir -p /project && chown bazinga:bazinga /project
WORKDIR /project

# Switch to non-root user
USER bazinga

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD bazinga version || exit 1

# Default entrypoint
ENTRYPOINT ["bazinga"]

# Default command (show help)
CMD ["--help"]
