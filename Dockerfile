FROM python:3.11-slim

# System dependency required by cfgrib
RUN apt-get update && apt-get install -y --no-install-recommends \
    libeccodes-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY src/ src/

# Pre-download the model cache on build (optional — avoids first-request delay)
RUN python -c "from src.inference import get_model; get_model()"

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
