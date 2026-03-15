# ---- Stage 1: Build environment ----
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src ./src

RUN uv sync --frozen
RUN uv pip install --no-deps .

# ---- Stage 2: Runtime ----
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /app/.venv ./.venv
COPY src ./src

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["python", "-m", "discord_lfg.bot"]
