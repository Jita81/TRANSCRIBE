# Multi-stage Dockerfile for Zeus EAA Compliance Tool Web API
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gnupg2 \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
    && rm kubectl

# Stage 2: Python dependencies
FROM base as python-deps

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY zeus-web-ui/requirements.txt /tmp/web-requirements.txt
COPY zeus-aks-integration/requirements.txt /tmp/integration-requirements.txt

# Install all requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/web-requirements.txt && \
    pip install --no-cache-dir -r /tmp/integration-requirements.txt

# Stage 3: Application
FROM base as app

# Copy virtual environment from previous stage
COPY --from=python-deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -r zeus && useradd -r -g zeus -u 1001 zeus

# Create application directories
RUN mkdir -p /app /app/cache /tmp && \
    chown -R zeus:zeus /app /tmp

# Copy application code
COPY --chown=zeus:zeus zeus-eaa-compliance-tool.py /app/
COPY --chown=zeus:zeus zeus-aks-integration/ /app/zeus-aks-integration/
COPY --chown=zeus:zeus zeus-web-ui/ /app/zeus-web-ui/

# Set working directory
WORKDIR /app

# Create symlink for easier imports
RUN ln -sf /app/zeus-aks-integration /app/zeus_aks_integration

# Switch to non-root user
USER zeus

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["python", "zeus-web-ui/api/main.py"]
