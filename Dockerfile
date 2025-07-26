FROM --platform=linux/amd64 python:3.13-slim

# System setup
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m appuser && \
    mkdir -p /app && \
    chown appuser:appuser /app

WORKDIR /app
USER appuser

# Set PATH before pip install
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Install packages
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy app code
COPY --chown=appuser:appuser src/ ./src/

# Create volumes
RUN mkdir -p /app/input /app/output

CMD ["python", "src/main.py"]
