FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libeccodes-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python dependencies (uv reads pyproject.toml)
COPY pyproject.toml .
RUN uv pip install --system --no-cache .

# Copy application code
COPY src/ src/

# Pre-load model at build time
RUN python -c "from src.inference import get_model; get_model()"

EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
