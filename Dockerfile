# ── Stage 1: Build ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build deps
RUN pip install --no-cache-dir build

# Copy only pyproject.toml first for dep caching
COPY pyproject.toml .
RUN pip wheel --no-cache-dir --wheel-dir /wheels "mcp>=1.2.0" "httpx>=0.28.0"

# Copy source
COPY src/ src/

# Build wheel
RUN python -m build --wheel --outdir /dist

# ── Stage 2: Runtime ────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy pre-built wheels and install
COPY --from=builder /wheels /wheels
COPY --from=builder /dist /dist
RUN pip install --no-cache-dir /dist/*.whl /wheels/*.whl && \
    rm -rf /wheels /dist

# Env defaults
ENV LOGAM_MULIA_BASE_URL=https://logam-mulia-api.iamutaki.workers.dev
ENV MCP_TRANSPORT=stdio
ENV HTTP_TIMEOUT=30

# Stdio transport — Claude Code / MCP host talks via stdin/stdout
ENTRYPOINT ["python", "-m", "logam_mulia_mcp.server"]

# SSE transport alternative:
#   ENV MCP_TRANSPORT=sse
#   EXPOSE 8080
#   CMD ["python", "-m", "logam_mulia_mcp.server"]
