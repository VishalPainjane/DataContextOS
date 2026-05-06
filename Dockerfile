FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Copy project definition
COPY pyproject.toml .

# Install dependencies
RUN uv pip install --system -e ".[prod]"

# Copy source code
COPY . .

# Expose API port
EXPOSE 8000
EXPOSE 8001

# Default command starts the API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
